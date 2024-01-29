# WeTheToolbox ⚒️

> ## *"The best tool to sell on WeTheNew"*

***

## 📖 Table of Contents

- [What is WeTheNew?](#-what-is-wethenew)
- [What is WeTheToolbox?](#-what-is-wethetoolbox)
- [How to install WeTheToolbox?](#-how-to-install-wethetoolbox)
- [How to contribute and contact us?](#-how-to-contribute-and-contact-us)

***

## 👟 What is WeTheNew?

WeTheNew, established in Paris in 2018 by David and Michael, two passionate sneaker enthusiasts, is a dedicated platform
revolutionizing the buying and selling experience of sneakers and streetwear in France. Recognizing the absence of a
quality, secure, and authentic platform in the market, WeTheNew emerged to cater to the growing demand for limited
edition sneakers and streetwear products.

With a team of over 130 sneaker lovers, WeTheNew has rapidly expanded from its initial duo to a major player in the
industry. Driven by the mission to provide sneaker and streetwear fans with a trustworthy platform to purchase limited
edition products, WeTheNew stands out in the market. The platform boasts an extensive network of tens of thousands of
partner retailers across Europe, ensuring a steady supply of sought-after, often instantly out-of-stock items, which are
then sold at premium prices.

WeTheNew is not just a [marketplace](https://wethenew.com/en); it's a project imbued with identity and voice, embracing
the motto "Process & Progress" from its inception. This spirit is evident in their commitment to offering the best
possible experience for those passionate about sneakers and streetwear.

## 🧰 What is WeTheToolbox?

A few years ago, WeTheNew launched the "Seller Space," an online platform enabling sneaker resellers to directly sell
their items to WeTheNew. This initiative quickly gained popularity due to WeTheNew's reputation for seriousness and
prompt payments. However, with many sellers eager to engage, offers on the platform are swiftly accepted, making it
challenging for individual sellers to successfully conclude deals.

In response to this, the open-source project WeTheToolbox was born. Its purpose is to level the playing field, offering
everyone an equal chance to enjoy the experience of selling to WeTheNew. WeTheToolbox features an aesthetic and
intuitive Command-Line Interface (CLI), simplifying the process of connecting with Europe's leading sneaker marketplace.

By joining the WeTheToolbox journey, sellers can now effortlessly tap into the bustling market of WeTheNew, enhancing
their chances of successful transactions in the competitive world of sneaker reselling.

### Our features (v1.4.0)

- [x] Monitor offers: get notified when a new offer is available on your seller space
- [x] Auto-accept offers: will automatically accept offers that meet your criteria
- [x] Monitor consignments: get notified when a new consignment is available
- [x] Auto-accept consignments: will automatically consign items from your listing
- [ ] List items: coming soon...

## 📦 How to install WeTheToolbox?

### Download the repository

You can download the repository by clicking on the green button "Code" and then "Download ZIP" or by using the following
command:

```shell
git clone https://github.com/Mathious6/WeTheToolbox.git
```

### Setup environment variables

To use WeTheToolbox, you need to have a [WeTheNew seller account](https://sell.wethenew.com/fr). If you don't have one,
you can create one. Once you have an account, you can use WeTheToolbox to monitor offers and consignments, auto-accept
offers, and list items. To do so, you need to provide your WeTheNew credentials to the toolbox. You can do this by
creating an `accounts.csv` file in the root directory of the project and filling it with your credentials following the
format `email,password,price_delta`. For example:

```csv
mail,password,price_delta
john.doe@gmail.com,my_password,10
pierre.doe@gmail.com,my_password,20
```

In this example, the toolbox will run 2 accounts and will accept offers up to 10€ below the listing price for the first
account and 20€ below the listing price for the second account.

You also need to create a `.env` file in the root directory of the project and fill it with the following variables:

```dotenv
MONITOR_DELAY=1.5
MONITOR_TIMEOUT=5
WEBHOOK_SUCCESS=your_webhook_success
WEBHOOK_REFUSED=your_webhook_refused
WEBHOOK_MONITOR=your_webhook_monitor
LOG_LEVEL=1
```

| Variable        | Type  | Optional | Description                                                   |
|-----------------|-------|----------|---------------------------------------------------------------|
| MONITOR_DELAY   | float | ❌        | The delay between each request to the API (in seconds)        |
| MONITOR_TIMEOUT | float | ❌        | The timeout of each request to the API (in seconds)           |
| WEBHOOK_SUCCESS | str   | ❌        | The webhook URL to send a message when an offer is accepted   |
| WEBHOOK_REFUSED | str   | ✔️       | The webhook URL to send a message when an offer is refused    |
| WEBHOOK_MONITOR | str   | ✔️       | The webhook URL to send a message when a consign is available |
| LOG_LEVEL       | int   | ✔️       | The level of the logs (0: all, 1: info, 2: warning, 3: error) |

### Install Python and dependencies

Then, you have to install the last Python version on the [official website](https://www.python.org/downloads/).

Finally, open a terminal in the root directory of the project and run the following command:

```shell
pip install -r requirements.txt
```

### Run the program

Add your proxies in the `proxies.txt` following the format `ip:port:username:password` and run the following command:

```shell
python main.py
```

## 🤝 How to contribute and contact us?

If you want to contribute to the project, you can fork the repository and create a pull request. You can also open an
issue if you have a suggestion or a bug to report. If you want to contact us or ask for support, you can join our
[Discord server](https://discord.gg/weyJWxD6Eb). We will be happy to help you!

Thanks to [@rawandahmad698](https://github.com/rawandahmad698) for
[noble-tls](https://github.com/rawandahmad698/noble-tls) and to WeTheNew for the API.
