type Listener = (data: any) => void;
export class EventBus {
  private listeners: Map<string, Listener[]> = new Map();
  subscribe(event: string, callback: Listener) {
    if (!this.listeners.has(event)) this.listeners.set(event, []);
    this.listeners.get(event)!.push(callback);
    return () => this.unsubscribe(event, callback);
  }
  unsubscribe(event: string, callback: Listener) {
    if (!this.listeners.has(event)) return;
    this.listeners.set(event, this.listeners.get(event)!.filter(cb => cb !== callback));
  }
  publish(event: string, data: any) {
    if (this.listeners.has(event)) this.listeners.get(event)!.forEach(cb => cb(data));
  }
}