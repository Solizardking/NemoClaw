"""Data Designer dataset configuration.

Builds the model + column config used for both preview and full generation
runs. Edit `build_config()` to change the schema of the generated dataset.
"""

import data_designer.config as dd


def build_config() -> "dd.DataDesignerConfigBuilder":
    model_configs = [
        dd.ModelConfig(
            provider="system/nvidia-build",
            model="nvidia/nemotron-3-nano-30b-a3b",
            alias="text",
            inference_parameters=dd.ChatCompletionInferenceParams(
                temperature=1.0,
                top_p=1.0,
            ),
        )
    ]

    config_builder = dd.DataDesignerConfigBuilder(model_configs)

    config_builder.add_column(
        dd.SamplerColumnConfig(
            name="category",
            sampler_type=dd.SamplerType.CATEGORY,
            params=dd.CategorySamplerParams(
                values=["Electronics", "Clothing", "Books"]
            ),
        )
    )

    config_builder.add_column(
        dd.LLMTextColumnConfig(
            name="product_name",
            prompt="Generate a creative product name for a {{ category }} product.",
            model_alias="text",
        )
    )

    return config_builder
