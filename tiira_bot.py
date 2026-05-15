def fetch_tampere_observations():
    response = requests.get(URL, timeout=30)
    response.encoding = "latin1"
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    text = soup.get_text("\n")

    raw_lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    allowed_dates = {today, yesterday}

    current_year = today.year
    current_date = None
    observations = []

    bird_species = None

    for line in raw_lines:
        date_match = re.fullmatch(r"(\d{1,2})\.(\d{1,2})\.", line)

        if date_match:
            day = int(date_match.group(1))
            month = int(date_match.group(2))
            current_date = datetime(current_year, month, day).date()
            bird_species = None
            continue

        if current_date not in allowed_dates:
            continue

        if line.startswith("("):
            continue

        if " " not in line:
            bird_species = line
            continue

        if "tampere" in line.lower():
            if bird_species:
                observations.append(f"{bird_species} {line}")
            else:
                observations.append(line)

    return observations
