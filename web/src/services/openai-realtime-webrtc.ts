/**
 * OpenAI Realtime API WebRTC Client
 *
 * This implements the current OpenAI recommended approach for browser-based
 * Realtime API connections using WebRTC instead of WebSocket.
 *
 * Based on: https://platform.openai.com/docs/guides/realtime-webrtc
 */

import { EventEmitter } from "events";

interface RealtimeConfig {
  apiKey: string;
  model?: string;
  voice?: string;
  instructions?: string;
  tools?: any[];
}

interface RTCSessionConfig {
  model: string;
  modalities: string[];
  instructions: string;
  voice: string;
  tools?: any[];
  turn_detection?: {
    type: string;
    threshold?: number;
    prefix_padding_ms?: number;
    silence_duration_ms?: number;
  };
  input_audio_transcription?: {
    model: string;
  };
}

export class OpenAIRealtimeWebRTC extends EventEmitter {
  private config: RealtimeConfig;
  private peerConnection: RTCPeerConnection | null = null;
  private dataChannel: RTCDataChannel | null = null;
  private connected = false;
  private ephemeralKey: string | null = null;

  constructor(config: RealtimeConfig) {
    super();
    this.config = {
      model: "gpt-4o-realtime-preview-2024-12-17",
      voice: "alloy",
      ...config,
    };
  }

  async connect(): Promise<void> {
    console.log("🚀 Starting OpenAI Realtime WebRTC connection...");
    try {
      // Step 1: Get ephemeral key from OpenAI
      console.log("Step 1/3: Getting ephemeral key...");
      await this.getEphemeralKey();
      console.log("✓ Step 1 complete: Got ephemeral key");

      // Step 2: Create WebRTC connection
      console.log("Step 2/3: Setting up WebRTC...");
      await this.setupWebRTC();
      console.log("✓ Step 2 complete: WebRTC setup done");

      // Step 3: Configure session
      console.log("Step 3/3: Configuring session...");
      await this.configureSession();
      console.log("✓ Step 3 complete: Session configured");

      this.connected = true;
      console.log("🎉 Successfully connected to OpenAI Realtime API!");
      this.emit("connected");
    } catch (error) {
      console.error("❌ Failed to connect to OpenAI Realtime API:", error);
      console.error("Stack trace:", error.stack);
      this.emit("error", error);
      throw error;
    }
  }

  private async getEphemeralKey(): Promise<void> {
    try {
      console.log("Getting ephemeral key from OpenAI...");
      const response = await fetch("https://api.openai.com/v1/realtime/sessions", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${this.config.apiKey}`,
          "Content-Type": "application/json",
          "OpenAI-Beta": "realtime=v1",
        },
        body: JSON.stringify({
          model: this.config.model,
          voice: this.config.voice,
        }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error("OpenAI API Error:", response.status, errorText);
        throw new Error(`Failed to get ephemeral key: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      console.log("Ephemeral key response:", data);
      this.ephemeralKey = data.client_secret.value;
    } catch (error) {
      console.error("Error getting ephemeral key:", error);
      throw error;
    }
  }

  private async setupWebRTC(): Promise<void> {
    console.log("🎯 Starting WebRTC setup...");

    // Create peer connection with STUN servers
    this.peerConnection = new RTCPeerConnection({
      iceServers: [
        { urls: "stun:stun.l.google.com:19302" },
        { urls: "stun:stun1.l.google.com:19302" },
      ],
    });
    console.log("✓ Created RTCPeerConnection");

    // Create data channel for events
    this.dataChannel = this.peerConnection.createDataChannel("oai-events", {
      ordered: true,
    });
    console.log("✓ Created data channel: oai-events");

    this.setupDataChannelEvents();
    this.setupPeerConnectionEvents();

    // Add audio track for microphone
    console.log("🎤 Requesting microphone access...");
    const stream = await navigator.mediaDevices.getUserMedia({
      audio: {
        channelCount: 1,
        sampleRate: 24000,
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
      },
    });
    console.log("✓ Got audio stream");

    stream.getTracks().forEach((track) => {
      this.peerConnection?.addTrack(track, stream);
      console.log(`✓ Added audio track: ${track.kind}`);
    });

    // Create offer and set local description
    console.log("📤 Creating WebRTC offer...");
    const offer = await this.peerConnection.createOffer();
    console.log("✓ Created offer, setting local description...");
    await this.peerConnection.setLocalDescription(offer);
    console.log("✓ Set local description");

    // Send offer to OpenAI - CORRECT ENDPOINT AND FORMAT
    const endpoint = `https://api.openai.com/v1/realtime?model=${this.config.model}`;
    console.log(`📡 Sending offer to OpenAI: ${endpoint}`);
    console.log("📋 Using ephemeral key:", `${this.ephemeralKey?.substring(0, 20)}...`);

    try {
      const response = await fetch(endpoint, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${this.ephemeralKey}`,
          "Content-Type": "application/sdp", // Not application/json!
        },
        body: offer.sdp, // Send raw SDP, not JSON!
      });

      console.log(`📥 OpenAI response status: ${response.status} ${response.statusText}`);

      if (!response.ok) {
        const errorText = await response.text();
        console.error("❌ OpenAI error response:", errorText);
        throw new Error(
          `Failed to connect WebRTC: ${response.status} ${response.statusText} - ${errorText}`
        );
      }

      const answerSdp = await response.text(); // Get raw SDP text, not JSON
      console.log("✓ Received answer SDP from OpenAI");
      console.log("📋 Answer SDP preview:", `${answerSdp.substring(0, 100)}...`);

      await this.peerConnection.setRemoteDescription({
        type: "answer",
        sdp: answerSdp,
      });
      console.log("✅ WebRTC setup complete!");
    } catch (error) {
      console.error("❌ Error during WebRTC setup:", error);
      throw error;
    }
  }

  private setupDataChannelEvents(): void {
    if (!this.dataChannel) return;

    this.dataChannel.onopen = () => {
      console.log("Data channel opened");
    };

    this.dataChannel.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.handleServerEvent(data);
      } catch (error) {
        console.error("Failed to parse server event:", error);
      }
    };

    this.dataChannel.onerror = (error) => {
      console.error("Data channel error:", error);
      this.emit("error", error);
    };

    this.dataChannel.onclose = () => {
      console.log("Data channel closed");
      this.connected = false;
      this.emit("disconnected");
    };
  }

  private setupPeerConnectionEvents(): void {
    if (!this.peerConnection) return;

    this.peerConnection.ontrack = (event) => {
      console.log("Received audio track from OpenAI");
      const audioElement = new Audio();
      audioElement.srcObject = event.streams[0];
      audioElement.play().catch(console.error);
    };

    this.peerConnection.oniceconnectionstatechange = () => {
      console.log("ICE connection state:", this.peerConnection?.iceConnectionState);
    };

    this.peerConnection.onconnectionstatechange = () => {
      console.log("Connection state:", this.peerConnection?.connectionState);
    };
  }

  private async configureSession(): Promise<void> {
    // Wait a bit for connection to stabilize
    await new Promise((resolve) => setTimeout(resolve, 1000));

    const sessionConfig: RTCSessionConfig = {
      model: this.config.model!,
      modalities: ["text", "audio"],
      instructions: this.config.instructions || "You are a helpful assistant.",
      voice: this.config.voice!,
      tools: this.config.tools || [],
      turn_detection: {
        type: "server_vad",
        threshold: 0.5,
        prefix_padding_ms: 300,
        silence_duration_ms: 200,
      },
      input_audio_transcription: {
        model: "whisper-1",
      },
    };

    console.log("🔧 Configuring session with instructions:", this.config.instructions);

    this.sendEvent({
      type: "session.update",
      session: sessionConfig,
    });

    // Send another update to make sure it sticks
    setTimeout(() => {
      console.log("🔧 Sending second session update with transcription enabled");
      this.sendEvent({
        type: "session.update",
        session: sessionConfig,
      });
    }, 2000);
  }

  private handleServerEvent(event: any): void {
    console.log("Server event:", event.type, event);

    switch (event.type) {
      case "session.created":
        this.emit("session.created", event);
        break;
      case "session.updated":
        this.emit("session.updated", event);
        break;
      case "response.audio_transcript.done":
        this.emit("response.audio_transcript.done", event);
        break;
      case "response.function_call_arguments.done":
        this.emit("response.function_call_arguments.done", event);
        break;
      case "input_audio_transcription.completed":
        this.emit("input_audio_transcription.completed", event);
        break;
      case "error":
        console.error("OpenAI Realtime API error:", event);
        this.emit("error", event);
        break;
      default:
        this.emit(event.type, event);
    }
  }

  sendEvent(event: any): void {
    if (!this.dataChannel || this.dataChannel.readyState !== "open") {
      console.warn("Data channel not ready, cannot send event:", event);
      return;
    }

    try {
      this.dataChannel.send(JSON.stringify(event));
    } catch (error) {
      console.error("Failed to send event:", error);
      this.emit("error", error);
    }
  }

  sendText(text: string): void {
    this.sendEvent({
      type: "conversation.item.create",
      item: {
        type: "message",
        role: "user",
        content: [{ type: "input_text", text }],
      },
    });

    this.sendEvent({ type: "response.create" });
  }

  isConnected(): boolean {
    return this.connected && this.dataChannel?.readyState === "open";
  }

  disconnect(): void {
    this.connected = false;

    if (this.dataChannel) {
      this.dataChannel.close();
      this.dataChannel = null;
    }

    if (this.peerConnection) {
      this.peerConnection.close();
      this.peerConnection = null;
    }

    this.emit("disconnected");
  }
}

export class AudioProcessor {
  private audioContext: AudioContext | null = null;

  private async getAudioContext(): Promise<AudioContext> {
    if (!this.audioContext) {
      this.audioContext = new AudioContext({ sampleRate: 24000 });

      // Resume context if suspended (autoplay policy)
      if (this.audioContext.state === "suspended") {
        await this.audioContext.resume();
      }
    }
    return this.audioContext;
  }

  async playPCM16(pcm16Data: ArrayBuffer): Promise<void> {
    const audioContext = await this.getAudioContext();

    // Convert PCM16 to Float32 for Web Audio API
    const int16Array = new Int16Array(pcm16Data);
    const float32Array = new Float32Array(int16Array.length);

    for (let i = 0; i < int16Array.length; i++) {
      float32Array[i] = int16Array[i] / 32768.0;
    }

    // Create audio buffer
    const audioBuffer = audioContext.createBuffer(1, float32Array.length, 24000);
    audioBuffer.getChannelData(0).set(float32Array);

    // Play audio
    const source = audioContext.createBufferSource();
    source.buffer = audioBuffer;
    source.connect(audioContext.destination);
    source.start();

    return new Promise((resolve) => {
      source.onended = () => resolve();
    });
  }

  float32ToPCM16(float32Array: Float32Array): ArrayBuffer {
    const int16Array = new Int16Array(float32Array.length);

    for (let i = 0; i < float32Array.length; i++) {
      const sample = Math.max(-1, Math.min(1, float32Array[i]));
      int16Array[i] = sample * 32767;
    }

    return int16Array.buffer;
  }

  destroy(): void {
    if (this.audioContext) {
      this.audioContext.close();
      this.audioContext = null;
    }
  }
}
