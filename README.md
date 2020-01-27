[![logo](https://raw.githubusercontent.com/dry-python/brand/master/logo/editors.png)](https://github.com/dry-python/editors)

[![azure-pipeline](https://dev.azure.com/dry-python/editors/_apis/build/status/dry-python.editors?branchName=master)](https://dev.azure.com/dry-python/editors/_build/latest?definitionId=2&branchName=master)
[![codecov](https://codecov.io/gh/dry-python/editors/branch/master/graph/badge.svg)](https://codecov.io/gh/dry-python/editors)
[![docs](https://readthedocs.org/projects/editors/badge/?version=latest)](https://editors.readthedocs.io/en/latest/?badge=latest)
[![gitter](https://badges.gitter.im/dry-python/editors.svg)](https://gitter.im/dry-python/editors)
[![pypi](https://img.shields.io/pypi/v/editors.svg)](https://pypi.python.org/pypi/editors/)
[![black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

---

## A set of tools to automate clients' code upgrade as much as possible.

- [Source Code](https://github.com/dry-python/editors)
- [Issue Tracker](https://github.com/dry-python/editors/issues)
- [Documentation](https://editors.readthedocs.io/en/latest/)
- [Discussion](https://gitter.im/dry-python/editors)

## Installation

```bash
pip install editors[stories]
```

## Stories Upgrade

Upgrade usage of stories DSL to a newer versions.

```bash
stories-upgrade $(git ls-files '*.py')
```

```diff
--- a/bookshelf/usecases/buy_subscription.py
+++ b/bookshelf/usecases/buy_subscription.py
@@ -45,17 +45,20 @@ class BuySubscription:
     def find_category(self, ctx):

         category = self.load_category(ctx.category_id)
-        return Success(category=category)
+        ctx.category = category
+        return Success()
```
