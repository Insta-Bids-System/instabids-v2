/**
 * OpenAI Realtime API WebSocket Client (Proxy-based)
 *
 * This uses a WebSocket proxy server to handle authentication since
 * browser WebSocket API doesn't support custom headers.
 */

import { EventEmitter } from "events";

interface RealtimeConfig {
  apiKey: string;
  model?: string;
  voice?: string;
  instructions?: string;
  tools?: any[];
}

interface SessionConfig {
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
  input_audio_format?: string;
  output_audio_format?: string;
  input_audio_transcription?: {
    model: string;
  };
}

export class OpenAIRealtimeWebSocket extends EventEmitter {
  private config: RealtimeConfig;
  private ws: WebSocket | null = null;
  private connected = false;

  constructor(config: RealtimeConfig) {
    super();
    this.config = {
      model: "gpt-4o-realtime-preview-2024-12-17",
      voice: "alloy",
      ...config,
    };
  }

  async connect(): Promise<void> {
    try {
      // Connect to our proxy WebSocket endpoint
      const backendUrl = import.meta.env.VITE_API_URL || "";
      const wsUrl = backendUrl.replace(/^http/, "ws");
      const url = `${wsUrl}/ws/realtime`;

      console.log("Connecting to WebSocket proxy:", url);
      this.ws = new WebSocket(url);

      this.setupWebSocketEvents();

      // Wait for connection
      await new Promise<void>((resolve, reject) => {
        const timeout = setTimeout(() => {
          reject(new Error("Connection timeout"));
        }, 10000);

        this.ws!.onopen = () => {
          clearTimeout(timeout);
          console.log("Connected to WebSocket proxy");
          this.connected = true;
          resolve();
        };

        this.ws!.onerror = (error) => {
          clearTimeout(timeout);
          console.error("WebSocket connection error:", error);
          reject(new Error("WebSocket connection failed"));
        };
      });

      // Configure the session
      await this.configureSession();

      this.emit("connected");
    } catch (error) {
      console.error("Failed to connect to OpenAI Realtime API:", error);
      this.emit("error", error);
      throw error;
    }
  }

  private setupWebSocketEvents(): void {
    if (!this.ws) return;

    this.ws.onopen = () => {
      console.log("WebSocket connection opened");
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.handleServerEvent(data);
      } catch (error) {
        console.error("Failed to parse server event:", error);
      }
    };

    this.ws.onerror = (error) => {
      console.error("WebSocket error:", error);
      this.emit("error", error);
    };

    this.ws.onclose = (event) => {
      console.log("WebSocket connection closed:", event.code, event.reason);
      this.connected = false;
      this.emit("disconnected");
    };
  }

  private async configureSession(): Promise<void> {
    const sessionConfig: SessionConfig = {
      model: this.config.model!,
      modalities: ["text", "audio"],
      instructions: this.config.instructions || "",
      voice: this.config.voice!,
      tools: this.config.tools || [],
      turn_detection: {
        type: "server_vad",
        threshold: 0.5,
        prefix_padding_ms: 300,
        silence_duration_ms: 200,
      },
      input_audio_format: "pcm16",
      output_audio_format: "pcm16",
      input_audio_transcription: {
        model: "whisper-1",
      },
    };

    this.sendEvent({
      type: "session.update",
      session: sessionConfig,
    });
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
      case "response.audio.done":
        this.emit("response.audio.done", event);
        break;
      case "conversation.item.input_audio_transcription.completed":
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
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.warn("WebSocket not ready, cannot send event:", event);
      return;
    }

    try {
      this.ws.send(JSON.stringify(event));
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

  sendAudio(audioData: ArrayBuffer): void {
    // Convert ArrayBuffer to base64
    const uint8Array = new Uint8Array(audioData);
    const base64 = btoa(String.fromCharCode.apply(null, Array.from(uint8Array)));

    this.sendEvent({
      type: "input_audio_buffer.append",
      audio: base64,
    });
  }

  commitAudio(): void {
    this.sendEvent({
      type: "input_audio_buffer.commit",
    });
  }

  clearAudio(): void {
    this.sendEvent({
      type: "input_audio_buffer.clear",
    });
  }

  isConnected(): boolean {
    return this.connected && this.ws?.readyState === WebSocket.OPEN;
  }

  disconnect(): void {
    this.connected = false;

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }

    this.emit("disconnected");
  }
}

export class AudioProcessor {
  private audioContext: AudioContext | null = null;
  private stream: MediaStream | null = null;
  private processor: ScriptProcessorNode | null = null;
  private isRecording = false;

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

  async startRecording(onAudioData: (data: ArrayBuffer) => void): Promise<void> {
    if (this.isRecording) return;

    const audioContext = await this.getAudioContext();

    this.stream = await navigator.mediaDevices.getUserMedia({
      audio: {
        channelCount: 1,
        sampleRate: 24000,
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
      },
    });

    const source = audioContext.createMediaStreamSource(this.stream);
    this.processor = audioContext.createScriptProcessor(4096, 1, 1);

    this.processor.onaudioprocess = (event) => {
      const inputBuffer = event.inputBuffer;
      const inputData = inputBuffer.getChannelData(0);

      // Convert Float32Array to PCM16
      const pcm16Data = this.float32ToPCM16(inputData);
      onAudioData(pcm16Data);
    };

    source.connect(this.processor);
    this.processor.connect(audioContext.destination);

    this.isRecording = true;
  }

  stopRecording(): void {
    if (!this.isRecording) return;

    if (this.processor) {
      this.processor.disconnect();
      this.processor = null;
    }

    if (this.stream) {
      this.stream.getTracks().forEach((track) => track.stop());
      this.stream = null;
    }

    this.isRecording = false;
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
    this.stopRecording();

    if (this.audioContext) {
      this.audioContext.close();
      this.audioContext = null;
    }
  }
}
