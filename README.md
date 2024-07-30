# CodeCloneAnalyzer

CodeCloneAnalyzer is an application designed to detect and analyze code clones within software repositories. It leverages advanced natural language processing techniques and pre-trained models to identify and measure the semantic similarity between different pieces of source code.

## Features
- Clone Detection: Identifies Type 1 (Exact), Type 2 (Renamed/Parameterized), Type 3 (Near-Miss), and Type 4 (Semantic) code clones.
- Repository Analysis: Clones and analyzes GitHub repositories based on specific tags.
- Preprocessing: Tokenizes and preprocesses source code files to prepare them for analysis.
- Semantic Analysis: Uses pre-trained models like fastText to compute embeddings and measure code similarity.
- User Interface: Provides an interface for users to input repository URLs, view clone detection results, and visualize similarities.
- Continuous Integration: Integrates with GitHub Actions to automate testing and deployment.

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/wasimsse/CodeCloneAnalyzer.git
   cd CodeCloneAnalyzer
