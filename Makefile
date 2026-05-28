PY ?= python

.PHONY: all fetch clean analyze anomaly app notebook reset

all: fetch clean analyze anomaly

fetch:
	$(PY) src/fetch_data.py

clean:
	$(PY) src/clean_data.py

analyze:
	$(PY) src/analyze.py

anomaly:
	$(PY) src/anomaly.py

app:
	streamlit run streamlit_app.py

notebook:
	$(PY) -m jupyter nbconvert --to notebook --execute --inplace \
		--ExecutePreprocessor.kernel_name=python3 notebooks/01_analysis.ipynb

reset:
	rm -rf data/raw data/processed reports/figures
