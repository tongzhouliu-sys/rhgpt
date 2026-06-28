// SSE parsing over a fetch ReadableStream (C7). Native EventSource cannot send
// the HMAC headers contract 3 requires, so we read the stream manually.

export interface SseFrame {
  id?: string;
  event?: string;
  data?: string;
}

/**
 * Read an SSE body, invoking `onFrame` per complete frame (separated by a blank
 * line). Returns true if the server sent `event: done` (stream complete), false
 * if the stream just ended (caller should reconnect with Last-Event-ID).
 * Comment lines (`: keepalive`) are ignored.
 */
export async function readSse(
  body: ReadableStream<Uint8Array>,
  onFrame: (frame: SseFrame) => void
): Promise<boolean> {
  const reader = body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let sawDone = false;

  try {
    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      let sep: number;
      while ((sep = buffer.indexOf("\n\n")) >= 0) {
        const rawFrame = buffer.slice(0, sep);
        buffer = buffer.slice(sep + 2);
        const frame = parseFrame(rawFrame);
        if (frame.event === "done") sawDone = true;
        onFrame(frame);
      }
    }
  } finally {
    reader.releaseLock();
  }
  return sawDone;
}

function parseFrame(raw: string): SseFrame {
  const frame: SseFrame = {};
  for (const line of raw.split("\n")) {
    if (!line || line.startsWith(":")) continue; // blank or comment (keepalive)
    if (line.startsWith("id:")) frame.id = line.slice(3).trim();
    else if (line.startsWith("event:")) frame.event = line.slice(6).trim();
    else if (line.startsWith("data:")) {
      const piece = line.slice(5).replace(/^ /, "");
      frame.data = frame.data === undefined ? piece : frame.data + "\n" + piece;
    }
  }
  return frame;
}
