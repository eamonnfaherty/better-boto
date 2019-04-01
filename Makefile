.PHONY: build publish


build:
	docker build . -t $(TAG)

publish:
	@echo "About to push"
	docker push $(TAG)

upload:
	python setup.py sdist
	pip install twine
	python -m twine upload --verbose dist/*

clean:
	rm -rf better_boto.egg-info
	rm -rf build
	rm -rf dist