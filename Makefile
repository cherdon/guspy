
env_setup: clean
	-@mkdir -p $(PKG_DIR)


test: clean_cache
	# NOTE: no pytest.ini, hence all options are given here
	pytest tests/ --junit-xml htmlcov/codecov-results.xml --cov-report xml --cov ./guspy --cov-config tests/.coveragerc --cov-report html

clean_cache:
	@echo Cleaning up ..
	rm -rf $(PKG_DIR) $(PROJECT_BASE_DIR)/*.rpm
	-find . -name *pyc -exec rm {} \;
	-find . -name "__pychache__" -exec rm -rf {} \;

clean:
	@echo Cleaning up ..
	rm -rf $(PKG_DIR) $(PROJECT_BASE_DIR)/*.rpm
	-find . -name *pyc -exec rm {} \;
	-find . -name "__pychache__" -exec rm -rf {} \;
    -rm -rf dist/
	-rm -rf build/
	-rm -rf *.egg-info*
	-rm -rf build/bdist*
	-rm -rf build/lib.*
	-rm coverage.xml
	-rm test_results.xml
	-rm -rf .cache/
	-rm -rf .coverage
	-rf -rf package

