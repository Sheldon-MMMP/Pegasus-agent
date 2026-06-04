import { EventEmitter, on } from "node:events";
import type { RunEvent } from "../domain/types.js";

interface Channel {
  emitter: EventEmitter;
  history: RunEvent[];
  closed: boolean;
}

class RunEventBroker {
  private readonly channels = new Map<string, Channel>();

  private getChannel(runId: string): Channel {
    let channel = this.channels.get(runId);
    if (!channel) {
      channel = { emitter: new EventEmitter(), history: [], closed: false };
      this.channels.set(runId, channel);
    }
    return channel;
  }

  publish(runId: string, event: RunEvent, terminal = false): void {
    const channel = this.getChannel(runId);
    channel.history.push(event);
    channel.emitter.emit("event", event);
    if (terminal) {
      channel.closed = true;
      channel.emitter.emit("closed");
    }
  }

  async *subscribe(runId: string): AsyncGenerator<RunEvent> {
    const channel = this.getChannel(runId);
    for (const event of channel.history) yield event;
    if (channel.closed) return;

    const controller = new AbortController();
    const events = on(channel.emitter, "event", { signal: controller.signal });
    const closed = new Promise<void>((resolve) =>
      channel.emitter.once("closed", resolve),
    );
    try {
      while (!channel.closed) {
        const result = await Promise.race([
          events.next(),
          closed.then(() => ({ done: true as const, value: undefined })),
        ]);
        if (result.done) return;
        yield result.value[0] as RunEvent;
      }
    } finally {
      controller.abort();
    }
  }
}

export const runEventBroker = new RunEventBroker();
