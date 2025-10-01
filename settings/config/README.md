Default configuration for the gateways.

Mount this folder as a configMap over /config to override these defaults.

To do this - create a folder called config in the same directory as your values.yaml file, and copy the contents of this folder into it.

Then, in your values.yaml file, add the following:

```yaml
overrideConfig: true
```