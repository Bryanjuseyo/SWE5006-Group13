class JobEventPublisher:
    def __init__(self):
        self._listeners = []

    def subscribe(self, listener):
        self._listeners.append(listener)

    def notify(self, event_name: str, job_request):
        for listener in self._listeners:
            listener.handle(event_name, job_request)
