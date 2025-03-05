# brainvisa_recipes

# Get started

You first have to install pyanatomist and pyaims. You can do it in two ways, either with the contained AppTainer or using pixi:

## The AppTainer way
Installation: you have to install the whole BrainVISA container. Please follow the instructions to download and install the **developper installation** given in <https://brainvisa.info/web/download.html>.

## The pixi way

You should first get pixi:

```curl -fsSL https://pixi.sh/install.sh | bash```

You then create a pixi environment (we place here this environment in the directory env_pixi):
```
mkdir env_pixi
cd env_pixi
pixi init -c conda-forge -c https://brainvisa.info/neuro-forge
pixi add anatomist soma-env=0.0 pip ipykernel
```

You then launch the environment:
```
pixi shell
```
# Content

| Software | Content |
| ------------- | ------------- |
| twin_game  | python code to launch the twin game, whose scope is to guess the right pair of brain twins  |
| notebooks  | Useful notebooks |
