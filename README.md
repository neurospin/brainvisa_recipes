# brainvisa_recipes

# Get started

You first have to install pyanatomist and pyaims. You can do this using pixi:

## The pixi way

You should first get pixi:

```
curl -fsSL https://pixi.sh/install.sh | bash
source ~/.bashrc
```

You then create a pixi environment (we place here this environment in the directory env_pixi) that contains anatomist:
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
| twin_game  | python code to launch the twin game, whose scope is to guess the correct pair of brain twins  |
| notebooks  | Useful notebooks |
