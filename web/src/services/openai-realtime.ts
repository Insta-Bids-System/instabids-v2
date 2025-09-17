import { EventEmitter } from "events";

interface RealtimeConfig {
  apiKey: string;
  model?: string;
  voice?: string;
  instructions?: string;
  tools?: Tool[];
}

interface Tool {
  type: "function";
  name: string;
  description: string;
  parameters: Record<string, any>;
}

interface RealtimeEvent {
  type: string;
  event_id?: string;
  [key: string]: any;
}

export class OpenAIRealtimeClient extends EventEmitter {
  private ws: WebSocket | null = null;
  private config: RealtimeConfig;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectTimeout = 1000;
  private isConnected = false;
  private audioBuffer: ArrayBuffer[] = [];

  constructor(config: RealtimeConfig) {
    super();
    this.config = {
      model: "gpt-4o-realtime-preview-2024-12-17",
      voice: "alloy",
      ...config,
    };
  }

  async connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        // Connect to our backend proxy which handles authentication
        const backendUrl = import.meta.env.VITE_API_URL || "";
        // Convert http to ws protocol
        const wsUrl = backendUrl.replace(/^http/, "ws");
        const url = `${wsUrl}/ws/realtime`;

        this.ws = new WebSocket(url);

        this.ws.onopen = () => {
          console.log("WebSocket connected to Realtime API proxy");
          this.isConnected = true;
          this.reconnectAttempts = 0;

          // Send session configuration
          this.send({
            type: "session.update",
            session: {
              modalities: ["text", "audio"],
              instructions: this.config.instructions || "",
              voice: this.config.voice,
              input_audio_format: "pcm16",
              output_audio_format: "pcm16",
              input_audio_transcription: {
                model: "whisper-1",
              },
              turn_detection: {
                type: "server_vad",
                threshold: 0.5,
                prefix_padding_ms: 300,
                silence_duration_ms: 500,
              },
              tools: this.config.tools || [],
              tool_choice: "auto",
            },
          });

          this.emit("connected");
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            this.handleEvent(data);
          } catch (error) {
            console.error("Failed to parse WebSocket message:", error);
          }
        };

        this.ws.onerror = (error) => {
          console.error("WebSocket error:", error);
          this.emit("error", error);
          reject(error);
        };

        this.ws.onclose = () => {
          console.log("WebSocket disconnected");
          this.isConnected = false;
          this.emit("disconnected");
          this.attemptReconnect();
        };
      } catch (error) {
        reject(error);
      }
    });
  }

  private handleEvent(event: RealtimeEvent) {
    console.log("Received event:", event.type);

    switch (event.type) {
      case "error":
        console.error("Server error:", event.error);
        this.emit("error", event.error);
        break;

      case "session.created":
        console.log("Session created:", event.session);
        this.emit("session.created", event.session);
        break;

      case "session.updated":
        console.log("Session updated:", event.session);
        this.emit("session.updated", event.session);
        break;

      case "conversation.item.created":
        this.emit("conversation.item.created", event.item);
        break;

      case "conversation.item.input_audio_transcription.completed":
        this.emit("input_audio_transcription.completed", event);
        break;

      case "response.created":
        this.emit("response.created", event.response);
        break;

      case "response.done":
        this.emit("response.done", event.response);
        break;

      case "response.output_item.added":
        this.emit("response.output_item.added", event.item);
        break;

      case "response.output_item.done":
        this.emit("response.output_item.done", event.item);
        break;

      case "response.audio_transcript.delta":
        this.emit("response.audio_transcript.delta", event);
        break;

      case "response.audio_transcript.done":
        this.emit("response.audio_transcript.done", event);
        break;

      case "response.audio.delta":
        // Handle audio chunk
        if (event.delta) {
          const audioData = this.base64ToArrayBuffer(event.delta);
          this.audioBuffer.push(audioData);
          this.emit("response.audio.delta", audioData);
        }
        break;

      case "response.audio.done": {
        // Audio response complete
        const completeAudio = this.mergeAudioBuffers(this.audioBuffer);
        this.audioBuffer = [];
        this.emit("response.audio.done", completeAudio);
        break;
      }

      case "response.function_call_arguments.delta":
        this.emit("response.function_call_arguments.delta", event);
        break;

      case "response.function_call_arguments.done":
        this.emit("response.function_call_arguments.done", event);
        break;

      case "input_audio_buffer.speech_started":
        this.emit("input_audio_buffer.speech_started", event);
        break;

      case "input_audio_buffer.speech_stopped":
        this.emit("input_audio_buffer.speech_stopped", event);
        break;

      case "input_audio_buffer.committed":
        this.emit("input_audio_buffer.committed", event);
        break;

      case "input_audio_buffer.cleared":
        this.emit("input_audio_buffer.cleared", event);
        break;

      default:
        this.emit(event.type, event);
    }
  }

  send(event: RealtimeEvent): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.error("WebSocket is not connected");
      return;
    }

    this.ws.send(JSON.stringify(event));
  }

  sendAudio(audioData: ArrayBuffer): void {
    // Convert ArrayBuffer to base64
    const base64Audio = this.arrayBufferToBase64(audioData);

    this.send({
      type: "input_audio_buffer.append",
      audio: base64Audio,
    });
  }

  commitAudio(): void {
    this.send({
      type: "input_audio_buffer.commit",
    });
  }

  clearAudio(): void {
    this.send({
      type: "input_audio_buffer.clear",
    });
  }

  sendText(text: string): void {
    this.send({
      type: "conversation.item.create",
      item: {
        type: "message",
        role: "user",
        content: [
          {
            type: "input_text",
            text: text,
          },
        ],
      },
    });

    // Trigger response
    this.createResponse();
  }

  createResponse(modalities: string[] = ["text", "audio"]): void {
    this.send({
      type: "response.create",
      response: {
        modalities: modalities,
        instructions: this.config.instructions,
      },
    });
  }

  cancelResponse(): void {
    this.send({
      type: "response.cancel",
    });
  }

  updateSession(session: Partial<any>): void {
    this.send({
      type: "session.update",
      session: session,
    });
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error("Max reconnection attempts reached");
      this.emit("max_reconnect_failed");
      return;
    }

    this.reconnectAttempts++;
    const timeout = this.reconnectTimeout * 2 ** (this.reconnectAttempts - 1);

    console.log(`Attempting to reconnect in ${timeout}ms (attempt ${this.reconnectAttempts})`);

    setTimeout(() => {
      this.connect().catch((error) => {
        console.error("Reconnection failed:", error);
      });
    }, timeout);
  }

  disconnect(): void {
    if (this.ws) {
      this.isConnected = false;
      this.ws.close();
      this.ws = null;
    }
  }

  isConnected(): boolean {
    return this.isConnected && this.ws?.readyState === WebSocket.OPEN;
  }

  private arrayBufferToBase64(buffer: ArrayBuffer): string {
    const bytes = new Uint8Array(buffer);
    let binary = "";
    for (let i = 0; i < bytes.byteLength; i++) {
      binary += String.fromCharCode(bytes[i]);
    }
    return btoa(binary);
  }

  private base64ToArrayBuffer(base64: string): ArrayBuffer {
    const binary = atob(base64);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) {
      bytes[i] = binary.charCodeAt(i);
    }
    return bytes.buffer;
  }

  private mergeAudioBuffers(buffers: ArrayBuffer[]): ArrayBuffer {
    const totalLength = buffers.reduce((sum, buf) => sum + buf.byteLength, 0);
    const result = new ArrayBuffer(totalLength);
    const view = new Uint8Array(result);

    let offset = 0;
    for (const buffer of buffers) {
      view.set(new Uint8Array(buffer), offset);
      offset += buffer.byteLength;
    }

    return result;
  }
}

// Audio utilities for PCM16 conversion
export class AudioProcessor {
  private audioContext: AudioContext;
  private sampleRate = 24000; // OpenAI Realtime expects 24kHz

  constructor() {
    this.audioContext = new AudioContext({ sampleRate: this.sampleRate });
  }

  async microphoneToBuffer(stream: MediaStream): Promise<AudioBuffer> {
    const source = this.audioContext.createMediaStreamSource(stream);
    const processor = this.audioContext.createScriptProcessor(4096, 1, 1);

    return new Promise((resolve) => {
      const chunks: Float32Array[] = [];

      processor.onaudioprocess = (e) => {
        const inputData = e.inputBuffer.getChannelData(0);
        chunks.push(new Float32Array(inputData));
      };

      source.connect(processor);
      processor.connect(this.audioContext.destination);

      // Return method to get current buffer
      (resolve as any).getBuffer = () => {
        const totalLength = chunks.reduce((sum, chunk) => sum + chunk.length, 0);
        const result = new Float32Array(totalLength);

        let offset = 0;
        for (const chunk of chunks) {
          result.set(chunk, offset);
          offset += chunk.length;
        }

        return this.float32ToPCM16(result);
      };
    });
  }

  float32ToPCM16(float32Array: Float32Array): ArrayBuffer {
    const buffer = new ArrayBuffer(float32Array.length * 2);
    const view = new DataView(buffer);

    for (let i = 0; i < float32Array.length; i++) {
      const sample = Math.max(-1, Math.min(1, float32Array[i]));
      view.setInt16(i * 2, sample * 0x7fff, true); // little-endian
    }

    return buffer;
  }

  pcm16ToFloat32(pcm16Buffer: ArrayBuffer): Float32Array {
    const view = new DataView(pcm16Buffer);
    const float32Array = new Float32Array(pcm16Buffer.byteLength / 2);

    for (let i = 0; i < float32Array.length; i++) {
      const sample = view.getInt16(i * 2, true); // little-endian
      float32Array[i] = sample / 0x7fff;
    }

    return float32Array;
  }

  async playPCM16(pcm16Buffer: ArrayBuffer): Promise<void> {
    const float32Data = this.pcm16ToFloat32(pcm16Buffer);
    const audioBuffer = this.audioContext.createBuffer(1, float32Data.length, this.sampleRate);
    audioBuffer.getChannelData(0).set(float32Data);

    const source = this.audioContext.createBufferSource();
    source.buffer = audioBuffer;
    source.connect(this.audioContext.destination);

    return new Promise((resolve) => {
      source.onended = () => resolve();
      source.start();
    });
  }
}
