[![logo](https://raw.githubusercontent.com/dry-python/brand/master/logo/editors.png)](https://github.com/dry-python/editors)

A set of tools to automate clients' code upgrade as much as possible.

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
