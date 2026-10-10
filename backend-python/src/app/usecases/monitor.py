from app.domain.entities.monitor import Monitor


class MonitorUsecase:
    def __init__(self, name: str, version: str) -> None:
        self._monitor = Monitor(name=name, version=version)

    def health_check(self) -> Monitor:
        return self._monitor
