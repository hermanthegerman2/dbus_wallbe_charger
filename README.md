# dbus_wallbe_charger
Module für Victron Venus OS

Install & Configuration
Get the code

Just grap a copy of the main branche and copy them to a folder under /data/ e.g. /data/dbus_wallbe_charger . After that call the install.sh script.

The following script should do everything for you:

wget https://github.com/hermanthegerman2/dbus_wallbe_charger/archive/refs/heads/main.zip
unzip main.zip "dbus_wallbe_charger -main/*" -d /data
mv /data/dbus_wallbe_charger -main /data/dbus_wallbe_charger
chmod a+x /data/dbus_wallbe_charger /install.sh
/data/dbus_wallbe_charger /install.sh
rm main.zip

⚠️ Check configuration after that - because service is already installed an running and with wrong connection data (host) you will spam the log-file
