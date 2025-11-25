from typing import Any

from app.core.reconstruction.base import BaseReconstructProvider
from app.core.logger import Logger


class NerfstudioReconstructProvider(BaseReconstructProvider):
    provider_code = 'nerfstudio'

    def __init__(
            self,
            input_dir: str | None = None,
            output_dir: str | None = None,
            cache_dir: str | None = None,
            logger: Logger | None = None,
            # config: NerfstudioConfigModel | None = None,
    ):
        super().__init__(input_dir, output_dir, cache_dir, logger)

    async def process(self, *args: Any, **kwargs: Any) -> str:
    #         import os
    # from nerfstudio.utils.eval_utils import eval_setup
    # from nerfstudio.exporter.exporter_utils import export_scene
    # from nerfstudio.engine.trainers import Trainer

    # # --------------------------
    # # Настройки
    # # --------------------------
    # DATA_DIR = "data/my_scene"  # папка с фото
    # OUTPUT_DIR = "outputs/my_scene"
    # TRAINER_NAME = "nerfacto"   # модель nerfacto
    # MESH_RESOLUTION = 256        # плотность mesh при Poisson
    # GLB_OUTPUT = os.path.join(OUTPUT_DIR, "scene.glb")

    # # --------------------------
    # # 1. Тренировка NeRF
    # # --------------------------
    # # Если хотим train полностью из Python
    # trainer = Trainer(
    #     train_data_dir=DATA_DIR,
    #     output_dir=OUTPUT_DIR,
    #     model_name=TRAINER_NAME,
    # )

    # # Запуск тренировки (GPU ускоряет сильно)
    # trainer.train(max_steps=5000)  # или меньше для быстрых тестов (~3-6 мин на 20 фото на RTX 4090)

    # # --------------------------
    # # 2. Подготовка пайплайна для экспорта
    # # --------------------------
    # # eval_setup подгружает модель и pipeline для рендеринга
    # config, pipeline, checkpoint = eval_setup(os.path.join(OUTPUT_DIR, TRAINER_NAME, "latest"))

    # # --------------------------
    # # 3. Экспорт в mesh + текстуры
    # # --------------------------
    # export_scene(
    #     pipeline=pipeline,
    #     output_dir=OUTPUT_DIR,
    #     export_type="gltf",      # "gltf" или "glb"
    #     mesh_resolution=MESH_RESOLUTION,
    #     bake_textures=True,      # делает UV и текстуры
    # )

    # print(f"Экспорт завершен! GLB находится в {OUTPUT_DIR}")

        return ""
