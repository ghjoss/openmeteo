WIFI_SSID = "router_wifi_ssid"
WIFI_PASSWORD = "router_wifi_password"
# 
OPEN_STREETMAP_AGENT = "OpenMeteoAPI_Weather/V1 (your_email@your_domain.com)"

"""
    Q: Does the user agent have to contain identifying information, such as the e-mail address?
    
    A:
    According to Nominatim's strict official Usage Policy, yes, it should ideally contain a way to contact you.

    While the server won't programmatically read your string and parse whether it's a real email address,
    their policy explicitly states that the User-Agent must be set to a "valid contact description." Here is
    why they want this, how to handle it safely, and an alternative if you don't want to expose your personal details:
    
    Why do they require it?

    Nominatim is a free, community-funded service run on donated hardware. If your script accidentally goes haywire
    (e.g., gets stuck in an infinite loop and bombards their servers with thousands of requests), system
    administrators look at the logs.

        If there is an email: They will often email you to ask you to fix the bug.

        If it's anonymous or generic: They will simply block your entire IP address or IP range from accessing the service completely.

    The Standard Format

    The ideal string format looks like this:
    Plaintext

    AppName/Version (YourEmailAddress or WebsiteURL)
    
"""
