# IMPC Data API Workshop Repository
Welcome to the IMPC Data API Workshop repository! This repository is designed to provide all the resources you need to follow along with our workshop on building and using data APIs. Below is an overview of the contents of this repository:
1. **Exercises**<br>
The `exercises` folder contains hands-on practice tasks and correct answers. If you would like to go through the exercises, use `impc_workshop_exercises.ipynb`. If you would like to look at the correct answers, take a look at `impc_workshop_answers.ipynb`.

2. **Presentations**<br>
The `presentations` folder includes all the slide decks used during the workshop sessions.

3. **Cheat Sheet**<br>
The `cheat_sheet.ipynb` file is a Jupyter Notebook that serves as a quick reference guide for common API tasks and commands.

### Useful Links
- [IMPC website](https://www.mousephenotype.org/)
- [IMPC SOLR cores documentation](https://www.ebi.ac.uk/mi/impc/solrdoc/)
- [IMPReSS](https://www.mousephenotype.org/impress/index) | International Mouse Phenotyping Resource of Standardised Screens
- [GenTaR](https://www.gentar.org/tracker/#/) | The Genome Targeting Repository<br>
### Phenodigm useful links:<br>
- [IMPC disease models summary](https://www.mousephenotype.org/help/data-visualization/gene-pages/disease-models/)
- [IMPC disease associations](https://www.mousephenotype.org/help/data-analysis/disease-associations/)
- [Disease Models Portal](https://diseasemodels.research.its.qmul.ac.uk)
- [OMIM](https://www.omim.org/) | Online Mendelian Inheritance in Man 
- [Orphanet](https://www.orpha.net)

# Installation Guide
Whether you attended the workshop or want to explore the exercises, here is a guide to work locally.
<br>
To use the Jupyter notebook with the exercises, you need to set up an environment to run it. We suggest two options:
1. **Local Installation (More control, but more setup)**: Install on your machine. This allows ease of access, execution of complex queries, and uses your computational resources, but can be challenging if you haven't used `pip` before. *We highly recommend this option*. 
2. **Using Binder (Easier to set up, but less resources available)**: A limited computing environment via [Binder](https://mybinder.org).

## Option 1. Local Installation with `pip` and Jupyter

We recommend using Python 3.10

1. **Create a virtual environment (optional but recommended)**:
   ```bash
   python3 -m venv my_venv
   source my_venv/bin/activate
   ```

2.  **Install Jupyter Notebook**:
   You can find the installation instructions [here](https://jupyter.org/install#jupyter-notebook). If you are using a virtual environment, make sure you install Jupyter notebook inside the environment. 

4. **Clone the repository**: Open your terminal and run:
   ```bash
   git clone https://github.com/mpi2/impc-data-api-workshop
   ```
5. **Update pip**:
   ```bash
   pip install --upgrade pip
   ```
6. **Install the dependencies**:
   ```bash
   cd impc-data-api-workshop
   pip install -r requirements.txt
   ```
7. **Start Jupyter Notebook**:
   ```bash
   jupyter notebook
   ```
8. This will open a new browser window with the Jupyter interface. On the sidebar, navigate to the exercises directory.
9. Open the `impc_workshop_exercises.ipynb` file.


## Option 2. Using Binder

If you prefer an easier way to interact with the material, try [Binder](https://mybinder.org)

We advice this approach for preliminary exploration of the material, if you wish to write your own queries we encourage you to attempt a the local setup.

1. Navigate to the Binder website.
2. Paste the URL of this repository as instructed.
3. This will start a Docker container with the dependencies from `requirements.txt`. All you have to do is wait.
4. Once it is done loading, a new window with a Jupyter notebook session will start.

**NOTES**:
   - Should you wish to save any changes you make to the Jupyter notebooks, follow Binder's instructions.
   - Binder has a maximum of simultaneous users per repo, to ensure you can use the material, opt for [Installation Option 1](#1-local-installation-with-pip-and-jupyter).
   - Note some of the existing queries in the exercises might not work due to the resource cap from Binder.


---

Happy coding! 
