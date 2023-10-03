import earthkit.data

print(earthkit.data.settings.get("number-of-download-threads"))

with earthkit.data.settings.temporary():
    earthkit.data.settings.set("number-of-download-threads", 12)
    print(earthkit.data.settings.get("number-of-download-threads"))

# Temporary settings can also be created with arguments:
with earthkit.data.settings.temporary("number-of-download-threads", 11):
    print(earthkit.data.settings.get("number-of-download-threads"))
