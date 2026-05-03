from dataclasses import dataclass


@dataclass(frozen=True)
class TrainingResult:
    status: str
    message: str


class TrainingService:
    async def save_and_train(self) -> TrainingResult:
        return TrainingResult(
            status="skipped",
            message="Данные сохранены. Индексация пропущена до настройки embeddings/API.",
        )
