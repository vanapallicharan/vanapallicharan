from morpho_core.ai_adapter import ai_talk


def generate_morpho_haiku(use_external: bool = False):
    return ai_talk("Write a haiku about Morpho, the evolving AI.", use_external=use_external)


if __name__ == "__main__":
    print(generate_morpho_haiku())
