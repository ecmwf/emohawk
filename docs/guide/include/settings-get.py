import earthkit.data

# Access one of the settings
cache_path = earthkit.data.settings.get("user-cache-directory")
print(cache_path)

# If this is the last line of a Notebook cell, this
# will display a table with all the current settings
earthkit.data.settings
