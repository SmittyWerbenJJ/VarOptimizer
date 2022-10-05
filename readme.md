VAM Optimizer
---
A tool to optimize .var files for virtamate by converting The Textures inside of the .var Archives

Features:
- Backing up .var Files inside folders
- Rescaling images to a desired Maximum Resolution from 128x128 to 4096x4096
- Recursive Operation of Nested AddonDirectories


![promo-pic](doc/promo.jpg)

<p>

---

#### Developer Notes

I use Vscode to develop this tool and Anaconda for package Management.

The environment can be created from the provided `environment.yml` file or by running the VSCodeTask `create conda environment`.

To build The Application you run the VSCodeTask called `make executable` and it will generate the executables inside of `dist\var-optimizer\`
