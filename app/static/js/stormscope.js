const StormScopeApp = (() => {
    const GLOBE_VIEW_WORLD = { lat: 18, lng: -25, altitude: 2.2 };
    const WEATHER_GAME_STORAGE_KEY = "stormscope-weather-duel-stats";
    const WATCHLIST_SNAPSHOT_LIMIT = 5;
    const WEATHER_CURRENT_CACHE_TTL_MS = 120000;
    const WEATHER_FORECAST_CACHE_TTL_MS = 600000;
    const WEATHER_CLIENT_CACHE_LIMIT = 150;
    const WEATHER_LOOKUP_SPACING_MS = 300;
    const EXPLORER_PENDING_CITY_STORAGE_KEY = "stormscope-pending-explorer-city";
    const WEATHER_GAME_CITIES = [
        { name: "Port of Spain", country: "Trinidad and Tobago", latitude: 10.6603, longitude: -61.5089, timezone: "America/Port_of_Spain" },
        { name: "Kingston", country: "Jamaica", latitude: 17.9712, longitude: -76.7936, timezone: "America/Jamaica" },
        { name: "Miami", country: "United States", latitude: 25.7617, longitude: -80.1918, timezone: "America/New_York" },
        { name: "Lima", country: "Peru", latitude: -12.0464, longitude: -77.0428, timezone: "America/Lima" },
        { name: "Mexico City", country: "Mexico", latitude: 19.4326, longitude: -99.1332, timezone: "America/Mexico_City" },
        { name: "Sao Paulo", country: "Brazil", latitude: -23.5505, longitude: -46.6333, timezone: "America/Sao_Paulo" },
        { name: "Buenos Aires", country: "Argentina", latitude: -34.6037, longitude: -58.3816, timezone: "America/Argentina/Buenos_Aires" },
        { name: "Reykjavik", country: "Iceland", latitude: 64.1466, longitude: -21.9426, timezone: "Atlantic/Reykjavik" },
        { name: "London", country: "United Kingdom", latitude: 51.5072, longitude: -0.1276, timezone: "Europe/London" },
        { name: "Cairo", country: "Egypt", latitude: 30.0444, longitude: 31.2357, timezone: "Africa/Cairo" },
        { name: "Mumbai", country: "India", latitude: 19.076, longitude: 72.8777, timezone: "Asia/Kolkata" },
        { name: "Singapore", country: "Singapore", latitude: 1.3521, longitude: 103.8198, timezone: "Asia/Singapore" },
        { name: "Tokyo", country: "Japan", latitude: 35.6762, longitude: 139.6503, timezone: "Asia/Tokyo" },
        { name: "Sydney", country: "Australia", latitude: -33.8688, longitude: 151.2093, timezone: "Australia/Sydney" },
        { name: "Ottawa", country: "Canada", latitude: 45.4215, longitude: -75.6972, timezone: "America/Toronto" },
        { name: "Paris", country: "France", latitude: 48.8566, longitude: 2.3522, timezone: "Europe/Paris" },
        { name: "Berlin", country: "Germany", latitude: 52.52, longitude: 13.405, timezone: "Europe/Berlin" },
        { name: "Madrid", country: "Spain", latitude: 40.4168, longitude: -3.7038, timezone: "Europe/Madrid" },
        { name: "Rome", country: "Italy", latitude: 41.9028, longitude: 12.4964, timezone: "Europe/Rome" },
        { name: "Lisbon", country: "Portugal", latitude: 38.7223, longitude: -9.1393, timezone: "Europe/Lisbon" },
        { name: "Amsterdam", country: "Netherlands", latitude: 52.3676, longitude: 4.9041, timezone: "Europe/Amsterdam" },
        { name: "Brussels", country: "Belgium", latitude: 50.8503, longitude: 4.3517, timezone: "Europe/Brussels" },
        { name: "Zurich", country: "Switzerland", latitude: 47.3769, longitude: 8.5417, timezone: "Europe/Zurich" },
        { name: "Vienna", country: "Austria", latitude: 48.2082, longitude: 16.3738, timezone: "Europe/Vienna" },
        { name: "Dublin", country: "Ireland", latitude: 53.3498, longitude: -6.2603, timezone: "Europe/Dublin" },
        { name: "Oslo", country: "Norway", latitude: 59.9139, longitude: 10.7522, timezone: "Europe/Oslo" },
        { name: "Stockholm", country: "Sweden", latitude: 59.3293, longitude: 18.0686, timezone: "Europe/Stockholm" },
        { name: "Helsinki", country: "Finland", latitude: 60.1699, longitude: 24.9384, timezone: "Europe/Helsinki" },
        { name: "Copenhagen", country: "Denmark", latitude: 55.6761, longitude: 12.5683, timezone: "Europe/Copenhagen" },
        { name: "Warsaw", country: "Poland", latitude: 52.2297, longitude: 21.0122, timezone: "Europe/Warsaw" },
        { name: "Prague", country: "Czech Republic", latitude: 50.0755, longitude: 14.4378, timezone: "Europe/Prague" },
        { name: "Budapest", country: "Hungary", latitude: 47.4979, longitude: 19.0402, timezone: "Europe/Budapest" },
        { name: "Athens", country: "Greece", latitude: 37.9838, longitude: 23.7275, timezone: "Europe/Athens" },
        { name: "Ankara", country: "Turkey", latitude: 39.9334, longitude: 32.8597, timezone: "Europe/Istanbul" },
        { name: "Kyiv", country: "Ukraine", latitude: 50.4501, longitude: 30.5234, timezone: "Europe/Kyiv" },
        { name: "Bucharest", country: "Romania", latitude: 44.4268, longitude: 26.1025, timezone: "Europe/Bucharest" },
        { name: "Sofia", country: "Bulgaria", latitude: 42.6977, longitude: 23.3219, timezone: "Europe/Sofia" },
        { name: "Zagreb", country: "Croatia", latitude: 45.815, longitude: 15.9819, timezone: "Europe/Zagreb" },
        { name: "Belgrade", country: "Serbia", latitude: 44.7866, longitude: 20.4489, timezone: "Europe/Belgrade" },
        { name: "Ljubljana", country: "Slovenia", latitude: 46.0569, longitude: 14.5058, timezone: "Europe/Ljubljana" },
        { name: "Bratislava", country: "Slovakia", latitude: 48.1486, longitude: 17.1077, timezone: "Europe/Bratislava" },
        { name: "Tallinn", country: "Estonia", latitude: 59.437, longitude: 24.7536, timezone: "Europe/Tallinn" },
        { name: "Riga", country: "Latvia", latitude: 56.9496, longitude: 24.1052, timezone: "Europe/Riga" },
        { name: "Vilnius", country: "Lithuania", latitude: 54.6872, longitude: 25.2797, timezone: "Europe/Vilnius" },
        { name: "Rabat", country: "Morocco", latitude: 34.0209, longitude: -6.8416, timezone: "Africa/Casablanca" },
        { name: "Algiers", country: "Algeria", latitude: 36.7538, longitude: 3.0588, timezone: "Africa/Algiers" },
        { name: "Tunis", country: "Tunisia", latitude: 36.8065, longitude: 10.1815, timezone: "Africa/Tunis" },
        { name: "Lagos", country: "Nigeria", latitude: 6.5244, longitude: 3.3792, timezone: "Africa/Lagos" },
        { name: "Accra", country: "Ghana", latitude: 5.6037, longitude: -0.187, timezone: "Africa/Accra" },
        { name: "Nairobi", country: "Kenya", latitude: -1.2921, longitude: 36.8219, timezone: "Africa/Nairobi" },
        { name: "Addis Ababa", country: "Ethiopia", latitude: 8.9806, longitude: 38.7578, timezone: "Africa/Addis_Ababa" },
        { name: "Johannesburg", country: "South Africa", latitude: -26.2041, longitude: 28.0473, timezone: "Africa/Johannesburg" },
        { name: "Dar es Salaam", country: "Tanzania", latitude: -6.7924, longitude: 39.2083, timezone: "Africa/Dar_es_Salaam" },
        { name: "Kampala", country: "Uganda", latitude: 0.3476, longitude: 32.5825, timezone: "Africa/Kampala" },
        { name: "Dakar", country: "Senegal", latitude: 14.7167, longitude: -17.4677, timezone: "Africa/Dakar" },
        { name: "Yaounde", country: "Cameroon", latitude: 3.848, longitude: 11.5021, timezone: "Africa/Douala" },
        { name: "Luanda", country: "Angola", latitude: -8.839, longitude: 13.2894, timezone: "Africa/Luanda" },
        { name: "Riyadh", country: "Saudi Arabia", latitude: 24.7136, longitude: 46.6753, timezone: "Asia/Riyadh" },
        { name: "Dubai", country: "United Arab Emirates", latitude: 25.2048, longitude: 55.2708, timezone: "Asia/Dubai" },
        { name: "Doha", country: "Qatar", latitude: 25.2854, longitude: 51.531, timezone: "Asia/Qatar" },
        { name: "Tel Aviv", country: "Israel", latitude: 32.0853, longitude: 34.7818, timezone: "Asia/Jerusalem" },
        { name: "Amman", country: "Jordan", latitude: 31.9539, longitude: 35.9106, timezone: "Asia/Amman" },
        { name: "Beirut", country: "Lebanon", latitude: 33.8938, longitude: 35.5018, timezone: "Asia/Beirut" },
        { name: "Baghdad", country: "Iraq", latitude: 33.3152, longitude: 44.3661, timezone: "Asia/Baghdad" },
        { name: "Tehran", country: "Iran", latitude: 35.6892, longitude: 51.389, timezone: "Asia/Tehran" },
        { name: "Karachi", country: "Pakistan", latitude: 24.8607, longitude: 67.0011, timezone: "Asia/Karachi" },
        { name: "Dhaka", country: "Bangladesh", latitude: 23.8103, longitude: 90.4125, timezone: "Asia/Dhaka" },
        { name: "Colombo", country: "Sri Lanka", latitude: 6.9271, longitude: 79.8612, timezone: "Asia/Colombo" },
        { name: "Kathmandu", country: "Nepal", latitude: 27.7172, longitude: 85.324, timezone: "Asia/Kathmandu" },
        { name: "Bangkok", country: "Thailand", latitude: 13.7563, longitude: 100.5018, timezone: "Asia/Bangkok" },
        { name: "Hanoi", country: "Vietnam", latitude: 21.0278, longitude: 105.8342, timezone: "Asia/Bangkok" },
        { name: "Kuala Lumpur", country: "Malaysia", latitude: 3.139, longitude: 101.6869, timezone: "Asia/Kuala_Lumpur" },
        { name: "Jakarta", country: "Indonesia", latitude: -6.2088, longitude: 106.8456, timezone: "Asia/Jakarta" },
        { name: "Manila", country: "Philippines", latitude: 14.5995, longitude: 120.9842, timezone: "Asia/Manila" },
        { name: "Seoul", country: "South Korea", latitude: 37.5665, longitude: 126.978, timezone: "Asia/Seoul" },
        { name: "Beijing", country: "China", latitude: 39.9042, longitude: 116.4074, timezone: "Asia/Shanghai" },
        { name: "Taipei", country: "Taiwan", latitude: 25.033, longitude: 121.5654, timezone: "Asia/Taipei" },
        { name: "Ulaanbaatar", country: "Mongolia", latitude: 47.8864, longitude: 106.9057, timezone: "Asia/Ulaanbaatar" },
        { name: "Almaty", country: "Kazakhstan", latitude: 43.2389, longitude: 76.8897, timezone: "Asia/Almaty" },
        { name: "Tashkent", country: "Uzbekistan", latitude: 41.2995, longitude: 69.2401, timezone: "Asia/Tashkent" },
        { name: "Auckland", country: "New Zealand", latitude: -36.8509, longitude: 174.7645, timezone: "Pacific/Auckland" },
        { name: "Suva", country: "Fiji", latitude: -18.1248, longitude: 178.4501, timezone: "Pacific/Fiji" },
        { name: "Port Moresby", country: "Papua New Guinea", latitude: -9.4438, longitude: 147.18, timezone: "Pacific/Port_Moresby" },
        { name: "Santiago", country: "Chile", latitude: -33.4489, longitude: -70.6693, timezone: "America/Santiago" },
        { name: "Bogota", country: "Colombia", latitude: 4.711, longitude: -74.0721, timezone: "America/Bogota" },
        { name: "Caracas", country: "Venezuela", latitude: 10.4806, longitude: -66.9036, timezone: "America/Caracas" },
        { name: "Quito", country: "Ecuador", latitude: -0.1807, longitude: -78.4678, timezone: "America/Guayaquil" },
        { name: "La Paz", country: "Bolivia", latitude: -16.4897, longitude: -68.1193, timezone: "America/La_Paz" },
        { name: "Asuncion", country: "Paraguay", latitude: -25.2637, longitude: -57.5759, timezone: "America/Asuncion" },
        { name: "Montevideo", country: "Uruguay", latitude: -34.9011, longitude: -56.1645, timezone: "America/Montevideo" },
        { name: "San Jose", country: "Costa Rica", latitude: 9.9281, longitude: -84.0907, timezone: "America/Costa_Rica" },
        { name: "Panama City", country: "Panama", latitude: 8.9824, longitude: -79.5199, timezone: "America/Panama" },
        { name: "Santo Domingo", country: "Dominican Republic", latitude: 18.4861, longitude: -69.9312, timezone: "America/Santo_Domingo" },
        { name: "Guatemala City", country: "Guatemala", latitude: 14.6349, longitude: -90.5069, timezone: "America/Guatemala" },
        { name: "Tegucigalpa", country: "Honduras", latitude: 14.0723, longitude: -87.1921, timezone: "America/Tegucigalpa" },
        { name: "San Salvador", country: "El Salvador", latitude: 13.6929, longitude: -89.2182, timezone: "America/El_Salvador" },
        { name: "Managua", country: "Nicaragua", latitude: 12.114, longitude: -86.2362, timezone: "America/Managua" },
        { name: "Havana", country: "Cuba", latitude: 23.1136, longitude: -82.3666, timezone: "America/Havana" },
        { name: "Georgetown", country: "Guyana", latitude: 6.8013, longitude: -58.1551, timezone: "America/Guyana" },
        { name: "Paramaribo", country: "Suriname", latitude: 5.852, longitude: -55.2038, timezone: "America/Paramaribo" },
        { name: "Nassau", country: "Bahamas", latitude: 25.0443, longitude: -77.3504, timezone: "America/Nassau" },
        { name: "Bridgetown", country: "Barbados", latitude: 13.0975, longitude: -59.6165, timezone: "America/Barbados" },
        { name: "St. John's", country: "Antigua and Barbuda", latitude: 17.1274, longitude: -61.8468, timezone: "America/Antigua" },
        { name: "Basseterre", country: "Saint Kitts and Nevis", latitude: 17.3026, longitude: -62.7177, timezone: "America/St_Kitts" },
        { name: "Castries", country: "Saint Lucia", latitude: 13.9094, longitude: -60.9789, timezone: "America/St_Lucia" },
        { name: "Kingstown", country: "Saint Vincent and the Grenadines", latitude: 13.1603, longitude: -61.2248, timezone: "America/St_Vincent" },
        { name: "St. George's", country: "Grenada", latitude: 12.0561, longitude: -61.7488, timezone: "America/Grenada" },
        { name: "Roseau", country: "Dominica", latitude: 15.3092, longitude: -61.3794, timezone: "America/Dominica" },
        { name: "Belmopan", country: "Belize", latitude: 17.251, longitude: -88.759, timezone: "America/Belize" },
        { name: "Port-au-Prince", country: "Haiti", latitude: 18.5944, longitude: -72.3074, timezone: "America/Port-au-Prince" },
        { name: "Tirana", country: "Albania", latitude: 41.3275, longitude: 19.8187, timezone: "Europe/Tirane" },
        { name: "Andorra la Vella", country: "Andorra", latitude: 42.5063, longitude: 1.5218, timezone: "Europe/Andorra" },
        { name: "Minsk", country: "Belarus", latitude: 53.9006, longitude: 27.559, timezone: "Europe/Minsk" },
        { name: "Sarajevo", country: "Bosnia and Herzegovina", latitude: 43.8563, longitude: 18.4131, timezone: "Europe/Sarajevo" },
        { name: "Nicosia", country: "Cyprus", latitude: 35.1856, longitude: 33.3823, timezone: "Asia/Nicosia" },
        { name: "Luxembourg", country: "Luxembourg", latitude: 49.6116, longitude: 6.1319, timezone: "Europe/Luxembourg" },
        { name: "Valletta", country: "Malta", latitude: 35.8989, longitude: 14.5146, timezone: "Europe/Malta" },
        { name: "Chisinau", country: "Moldova", latitude: 47.0105, longitude: 28.8638, timezone: "Europe/Chisinau" },
        { name: "Podgorica", country: "Montenegro", latitude: 42.4304, longitude: 19.2594, timezone: "Europe/Podgorica" },
        { name: "Skopje", country: "North Macedonia", latitude: 41.9973, longitude: 21.428, timezone: "Europe/Skopje" },
        { name: "Moscow", country: "Russia", latitude: 55.7558, longitude: 37.6173, timezone: "Europe/Moscow" },
        { name: "San Marino", country: "San Marino", latitude: 43.9424, longitude: 12.4578, timezone: "Europe/Rome" },
        { name: "Monaco", country: "Monaco", latitude: 43.7384, longitude: 7.4246, timezone: "Europe/Monaco" },
        { name: "Vaduz", country: "Liechtenstein", latitude: 47.141, longitude: 9.5209, timezone: "Europe/Vaduz" },
        { name: "Vatican City", country: "Vatican City", latitude: 41.9029, longitude: 12.4534, timezone: "Europe/Rome" },
        { name: "Yerevan", country: "Armenia", latitude: 40.1792, longitude: 44.4991, timezone: "Asia/Yerevan" },
        { name: "Baku", country: "Azerbaijan", latitude: 40.4093, longitude: 49.8671, timezone: "Asia/Baku" },
        { name: "Tbilisi", country: "Georgia", latitude: 41.7151, longitude: 44.8271, timezone: "Asia/Tbilisi" },
        { name: "Tripoli", country: "Libya", latitude: 32.8872, longitude: 13.1913, timezone: "Africa/Tripoli" },
        { name: "Khartoum", country: "Sudan", latitude: 15.5007, longitude: 32.5599, timezone: "Africa/Khartoum" },
        { name: "Juba", country: "South Sudan", latitude: 4.8594, longitude: 31.5713, timezone: "Africa/Juba" },
        { name: "Asmara", country: "Eritrea", latitude: 15.3229, longitude: 38.9251, timezone: "Africa/Asmara" },
        { name: "Djibouti", country: "Djibouti", latitude: 11.5721, longitude: 43.1456, timezone: "Africa/Djibouti" },
        { name: "Mogadishu", country: "Somalia", latitude: 2.0469, longitude: 45.3182, timezone: "Africa/Mogadishu" },
        { name: "Kigali", country: "Rwanda", latitude: -1.9441, longitude: 30.0619, timezone: "Africa/Kigali" },
        { name: "Gitega", country: "Burundi", latitude: -3.4264, longitude: 29.9306, timezone: "Africa/Bujumbura" },
        { name: "Kinshasa", country: "Democratic Republic of the Congo", latitude: -4.4419, longitude: 15.2663, timezone: "Africa/Kinshasa" },
        { name: "Brazzaville", country: "Republic of the Congo", latitude: -4.2634, longitude: 15.2429, timezone: "Africa/Brazzaville" },
        { name: "Libreville", country: "Gabon", latitude: 0.4162, longitude: 9.4673, timezone: "Africa/Libreville" },
        { name: "Malabo", country: "Equatorial Guinea", latitude: 3.7504, longitude: 8.7371, timezone: "Africa/Malabo" },
        { name: "Sao Tome", country: "Sao Tome and Principe", latitude: 0.3365, longitude: 6.7273, timezone: "Africa/Sao_Tome" },
        { name: "Lome", country: "Togo", latitude: 6.1725, longitude: 1.2314, timezone: "Africa/Lome" },
        { name: "Porto-Novo", country: "Benin", latitude: 6.4969, longitude: 2.6289, timezone: "Africa/Porto-Novo" },
        { name: "Ouagadougou", country: "Burkina Faso", latitude: 12.3714, longitude: -1.5197, timezone: "Africa/Ouagadougou" },
        { name: "Abidjan", country: "Cote d'Ivoire", latitude: 5.35995, longitude: -4.0083, timezone: "Africa/Abidjan" },
        { name: "Monrovia", country: "Liberia", latitude: 6.3156, longitude: -10.8074, timezone: "Africa/Monrovia" },
        { name: "Freetown", country: "Sierra Leone", latitude: 8.4657, longitude: -13.2317, timezone: "Africa/Freetown" },
        { name: "Conakry", country: "Guinea", latitude: 9.6412, longitude: -13.5784, timezone: "Africa/Conakry" },
        { name: "Bissau", country: "Guinea-Bissau", latitude: 11.8817, longitude: -15.617, timezone: "Africa/Bissau" },
        { name: "Nouakchott", country: "Mauritania", latitude: 18.0735, longitude: -15.9582, timezone: "Africa/Nouakchott" },
        { name: "Bamako", country: "Mali", latitude: 12.6392, longitude: -8.0029, timezone: "Africa/Bamako" },
        { name: "Niamey", country: "Niger", latitude: 13.5116, longitude: 2.1254, timezone: "Africa/Niamey" },
        { name: "N'Djamena", country: "Chad", latitude: 12.1348, longitude: 15.0557, timezone: "Africa/Ndjamena" },
        { name: "Bangui", country: "Central African Republic", latitude: 4.3947, longitude: 18.5582, timezone: "Africa/Bangui" },
        { name: "Windhoek", country: "Namibia", latitude: -22.5609, longitude: 17.0658, timezone: "Africa/Windhoek" },
        { name: "Gaborone", country: "Botswana", latitude: -24.6282, longitude: 25.9231, timezone: "Africa/Gaborone" },
        { name: "Lusaka", country: "Zambia", latitude: -15.3875, longitude: 28.3228, timezone: "Africa/Lusaka" },
        { name: "Harare", country: "Zimbabwe", latitude: -17.8252, longitude: 31.0335, timezone: "Africa/Harare" },
        { name: "Maputo", country: "Mozambique", latitude: -25.9692, longitude: 32.5732, timezone: "Africa/Maputo" },
        { name: "Antananarivo", country: "Madagascar", latitude: -18.8792, longitude: 47.5079, timezone: "Indian/Antananarivo" },
        { name: "Lilongwe", country: "Malawi", latitude: -13.9626, longitude: 33.7741, timezone: "Africa/Blantyre" },
        { name: "Maseru", country: "Lesotho", latitude: -29.3151, longitude: 27.4869, timezone: "Africa/Maseru" },
        { name: "Mbabane", country: "Eswatini", latitude: -26.3054, longitude: 31.1367, timezone: "Africa/Mbabane" },
        { name: "Victoria", country: "Seychelles", latitude: -4.6191, longitude: 55.4513, timezone: "Indian/Mahe" },
        { name: "Moroni", country: "Comoros", latitude: -11.7172, longitude: 43.2473, timezone: "Indian/Comoro" },
        { name: "Port Louis", country: "Mauritius", latitude: -20.1609, longitude: 57.5012, timezone: "Indian/Mauritius" },
        { name: "Praia", country: "Cape Verde", latitude: 14.9331, longitude: -23.5133, timezone: "Atlantic/Cape_Verde" },
        { name: "Banjul", country: "Gambia", latitude: 13.4549, longitude: -16.579, timezone: "Africa/Banjul" },
        { name: "Muscat", country: "Oman", latitude: 23.588, longitude: 58.3829, timezone: "Asia/Muscat" },
        { name: "Sanaa", country: "Yemen", latitude: 15.3694, longitude: 44.191, timezone: "Asia/Aden" },
        { name: "Kuwait City", country: "Kuwait", latitude: 29.3759, longitude: 47.9774, timezone: "Asia/Kuwait" },
        { name: "Manama", country: "Bahrain", latitude: 26.2235, longitude: 50.5876, timezone: "Asia/Bahrain" },
        { name: "Damascus", country: "Syria", latitude: 33.5138, longitude: 36.2765, timezone: "Asia/Damascus" },
        { name: "Kabul", country: "Afghanistan", latitude: 34.5553, longitude: 69.2075, timezone: "Asia/Kabul" },
        { name: "Ashgabat", country: "Turkmenistan", latitude: 37.9601, longitude: 58.3261, timezone: "Asia/Ashgabat" },
        { name: "Bishkek", country: "Kyrgyzstan", latitude: 42.8746, longitude: 74.5698, timezone: "Asia/Bishkek" },
        { name: "Dushanbe", country: "Tajikistan", latitude: 38.5598, longitude: 68.787, timezone: "Asia/Dushanbe" },
        { name: "Thimphu", country: "Bhutan", latitude: 27.4728, longitude: 89.639, timezone: "Asia/Thimphu" },
        { name: "Male", country: "Maldives", latitude: 4.1755, longitude: 73.5093, timezone: "Indian/Maldives" },
        { name: "Pyongyang", country: "North Korea", latitude: 39.0392, longitude: 125.7625, timezone: "Asia/Pyongyang" },
        { name: "Vientiane", country: "Laos", latitude: 17.9757, longitude: 102.6331, timezone: "Asia/Vientiane" },
        { name: "Phnom Penh", country: "Cambodia", latitude: 11.5564, longitude: 104.9282, timezone: "Asia/Phnom_Penh" },
        { name: "Bandar Seri Begawan", country: "Brunei", latitude: 4.9031, longitude: 114.9398, timezone: "Asia/Brunei" },
        { name: "Dili", country: "Timor-Leste", latitude: -8.5569, longitude: 125.5603, timezone: "Asia/Dili" },
        { name: "Yangon", country: "Myanmar", latitude: 16.8409, longitude: 96.1735, timezone: "Asia/Yangon" },
        { name: "Apia", country: "Samoa", latitude: -13.8333, longitude: -171.7667, timezone: "Pacific/Apia" },
        { name: "Nuku'alofa", country: "Tonga", latitude: -21.1394, longitude: -175.2049, timezone: "Pacific/Tongatapu" },
        { name: "Port Vila", country: "Vanuatu", latitude: -17.7334, longitude: 168.3273, timezone: "Pacific/Efate" },
        { name: "Honiara", country: "Solomon Islands", latitude: -9.4456, longitude: 159.9729, timezone: "Pacific/Guadalcanal" },
        { name: "Tarawa", country: "Kiribati", latitude: 1.4518, longitude: 173.0348, timezone: "Pacific/Tarawa" },
        { name: "Palikir", country: "Micronesia", latitude: 6.9248, longitude: 158.1611, timezone: "Pacific/Pohnpei" },
        { name: "Ngerulmud", country: "Palau", latitude: 7.5006, longitude: 134.6242, timezone: "Pacific/Palau" },
        { name: "Majuro", country: "Marshall Islands", latitude: 7.0897, longitude: 171.3803, timezone: "Pacific/Majuro" },
        { name: "Yaren", country: "Nauru", latitude: -0.5477, longitude: 166.9209, timezone: "Pacific/Nauru" },
        { name: "Funafuti", country: "Tuvalu", latitude: -8.5211, longitude: 179.1962, timezone: "Pacific/Funafuti" },
    ];
    const state = {
        globe: null,
        detailMap: null,
        detailMarker: null,
        detailCircle: null,
        selectedCity: null,
        currentUser: null,
        nasaEvents: [],
        nasaFilter: "all",
        watchlist: [],
        disasters: [],
        users: [],
        logoModalPreviouslyFocused: null,
        weatherGame: {
            score: 0,
            rounds: 0,
            streak: 0,
            currentRound: null,
            loading: false,
        },
    };
    const weatherResponseCache = {
        current: new Map(),
        forecast: new Map(),
    };
    let weatherLookupQueue = Promise.resolve();

    function showToast(title, message) {
        const toastElement = document.getElementById("appToast");
        if (!toastElement || !window.bootstrap) return;
        document.getElementById("toastTitle").textContent = title;
        document.getElementById("toastContent").textContent = message;
        bootstrap.Toast.getOrCreateInstance(toastElement).show();
    }

    async function api(url, options = {}) {
        const headers = options.body ? { "Content-Type": "application/json" } : {};
        const response = await fetch(url, { ...options, headers: { ...headers, ...(options.headers || {}) } });
        if (response.status === 204) return null;
        const payload = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(payload.detail || "Request failed");
        return payload;
    }

    function formatDate(value) {
        if (!value) return "Unknown";
        const parsed = value.includes("T") ? new Date(value) : new Date(`${value}T00:00:00`);
        if (Number.isNaN(parsed.getTime())) return value;
        return parsed.toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });
    }

    function formatDateTime(value) {
        if (!value) return "Unknown";
        const parsed = new Date(value);
        if (Number.isNaN(parsed.getTime())) return value;
        return parsed.toLocaleString(undefined, {
            month: "short",
            day: "numeric",
            year: "numeric",
            hour: "numeric",
            minute: "2-digit",
        });
    }

    function escapeHtml(value) {
        return String(value ?? "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#39;");
    }

    function formatUserRole(role) {
        return String(role || "regular_user").replace(/_/g, " ");
    }

    function getCurrentSessionUserId() {
        return Number(document.getElementById("currentSessionUserId")?.value || 0);
    }

    function syncCurrentSessionUser(user) {
        if (!user) return;
        state.currentUser = user;
        const currentSessionUserId = document.getElementById("currentSessionUserId");
        const currentSessionUsername = document.getElementById("currentSessionUsername");
        const currentSessionUserRole = document.getElementById("currentSessionUserRole");
        const currentSessionDisplayName = document.getElementById("currentSessionDisplayName");
        const currentSessionDisplayRole = document.getElementById("currentSessionDisplayRole");

        if (currentSessionUserId) currentSessionUserId.value = String(user.id);
        if (currentSessionUsername) currentSessionUsername.value = user.username || "";
        if (currentSessionUserRole) currentSessionUserRole.value = user.role || "";
        if (currentSessionDisplayName) currentSessionDisplayName.textContent = user.username || "";
        if (currentSessionDisplayRole) currentSessionDisplayRole.textContent = formatUserRole(user.role);
    }

    function isMobileViewport() {
        return window.innerWidth <= 991;
    }

    function setMobileNavOpen(isOpen) {
        const body = document.body;
        const toggle = document.getElementById("mobileNavToggle");
        if (!body || !toggle) return;

        const shouldOpen = Boolean(isOpen) && isMobileViewport();
        body.classList.toggle("stormscope-mobile-nav-open", shouldOpen);
        toggle.setAttribute("aria-expanded", shouldOpen ? "true" : "false");
    }

    function closeMobileNav() {
        setMobileNavOpen(false);
    }

    function toggleMobileNav() {
        const isOpen = document.body?.classList.contains("stormscope-mobile-nav-open");
        setMobileNavOpen(!isOpen);
    }

    function setLogoModalOpen(isOpen) {
        const modal = document.getElementById("stormscopeLogoModal");
        const trigger = document.getElementById("stormscopeLogoTrigger");
        if (!modal) return;

        const shouldOpen = Boolean(isOpen);
        if (shouldOpen) {
            closeMobileNav();
            state.logoModalPreviouslyFocused = document.activeElement instanceof HTMLElement ? document.activeElement : null;
        }

        document.body?.classList.toggle("stormscope-logo-modal-open", shouldOpen);
        modal.hidden = !shouldOpen;
        modal.setAttribute("aria-hidden", shouldOpen ? "false" : "true");
        if (trigger) {
            trigger.setAttribute("aria-expanded", shouldOpen ? "true" : "false");
        }

        if (shouldOpen) {
            document.getElementById("stormscopeLogoModalClose")?.focus();
            return;
        }

        if (state.logoModalPreviouslyFocused?.isConnected) {
            state.logoModalPreviouslyFocused.focus();
        }
        state.logoModalPreviouslyFocused = null;
    }

    function openLogoModal() {
        setLogoModalOpen(true);
    }

    function closeLogoModal() {
        setLogoModalOpen(false);
    }

    function syncMobileNavForViewport() {
        if (!isMobileViewport()) {
            closeMobileNav();
        }
    }

    function loadWeatherGameStats() {
        try {
            const stored = JSON.parse(window.localStorage.getItem(WEATHER_GAME_STORAGE_KEY) || "{}");
            state.weatherGame.score = Number(stored.score) || 0;
            state.weatherGame.rounds = Number(stored.rounds) || 0;
            state.weatherGame.streak = Number(stored.streak) || 0;
        } catch (error) {
            state.weatherGame.score = 0;
            state.weatherGame.rounds = 0;
            state.weatherGame.streak = 0;
        }
    }

    function persistWeatherGameStats() {
        try {
            window.localStorage.setItem(
                WEATHER_GAME_STORAGE_KEY,
                JSON.stringify({
                    score: state.weatherGame.score,
                    rounds: state.weatherGame.rounds,
                    streak: state.weatherGame.streak,
                })
            );
        } catch (error) {
            
        }
    }

    function renderWeatherGameStats() {
        const score = document.getElementById("weatherGameScore");
        const rounds = document.getElementById("weatherGameRounds");
        const streak = document.getElementById("weatherGameStreak");
        if (score) score.textContent = String(state.weatherGame.score);
        if (rounds) rounds.textContent = String(state.weatherGame.rounds);
        if (streak) streak.textContent = String(state.weatherGame.streak);
    }

    function setWeatherGamePrompt(text) {
        const prompt = document.getElementById("weatherGamePrompt");
        if (prompt) prompt.textContent = text;
    }

    function normalizeExplorerCity(city) {
        if (!city) return null;
        return {
            name: city.name || city.city_name,
            country: city.country || city.country_name,
            latitude: city.latitude,
            longitude: city.longitude,
            timezone: city.timezone || "auto",
            admin1: city.admin1 || null,
            feature_code: city.feature_code || null,
        };
    }

    function getWeatherIconClass(weatherCode, isDay = true) {
        const code = Number(weatherCode);
        if (code === 0) return isDay ? "fa-solid fa-sun" : "fa-solid fa-moon";
        if ([1, 2].includes(code)) return isDay ? "fa-solid fa-cloud-sun" : "fa-solid fa-cloud-moon";
        if (code === 3) return "fa-solid fa-cloud";
        if ([45, 48].includes(code)) return "fa-solid fa-smog";
        if ([51, 53, 55].includes(code)) return "fa-solid fa-cloud-rain";
        if ([61, 63, 65, 80, 81, 82].includes(code)) return "fa-solid fa-cloud-showers-heavy";
        if ([71, 73, 75].includes(code)) return "fa-solid fa-snowflake";
        if ([95, 96, 99].includes(code)) return "fa-solid fa-bolt";
        return "fa-solid fa-cloud";
    }

    function renderWeatherIcon(weatherCode, isDay = true, className = "weather-icon-badge") {
        return `<span class="${className}" aria-hidden="true"><i class="${getWeatherIconClass(weatherCode, isDay)}"></i></span>`;
    }

    function renderDataLine(label, value, iconClass = null) {
        const labelMarkup = iconClass
            ? `<span class="data-label-with-icon"><i class="${iconClass} weather-inline-icon" aria-hidden="true"></i><span>${label}</span></span>`
            : `<span>${label}</span>`;
        return `
            <div class="data-line">
                ${labelMarkup}
                <strong>${value}</strong>
            </div>
        `;
    }

    function renderWeatherLabel(weather, className = "weather-inline-label") {
        return `
            <span class="${className}">
                <i class="${getWeatherIconClass(weather.weather_code, weather.is_day)} weather-inline-icon" aria-hidden="true"></i>
                <span>${weather.weather_label}</span>
            </span>
        `;
    }

    function queuePendingExplorerCity(city) {
        const normalizedCity = normalizeExplorerCity(city);
        if (!normalizedCity) return;
        try {
            window.sessionStorage.setItem(EXPLORER_PENDING_CITY_STORAGE_KEY, JSON.stringify(normalizedCity));
        } catch (error) {
            // Ignore storage failures and fall back to navigation without preselection.
        }
    }

    function consumePendingExplorerCity() {
        try {
            const raw = window.sessionStorage.getItem(EXPLORER_PENDING_CITY_STORAGE_KEY);
            if (!raw) return null;
            window.sessionStorage.removeItem(EXPLORER_PENDING_CITY_STORAGE_KEY);
            return normalizeExplorerCity(JSON.parse(raw));
        } catch (error) {
            return null;
        }
    }

    function renderWeatherGameTimer() {
        const timer = document.getElementById("weatherGameTimer");
        const revealTimer = document.getElementById("weatherGameRevealTimer");
        if (!timer && !revealTimer) return;

        let text = "Start a duel when you want a fresh saved comparison.";
        let active = false;

        if (state.weatherGame.loading) {
            text = "Preparing the next duel now...";
            active = true;
        } else if (state.weatherGame.currentRound?.resolved) {
            text = "Round finished. Click New Duel for another comparison.";
        } else if (state.weatherGame.currentRound) {
            text = "Make your pick to finish this duel.";
        }

        if (timer) {
            timer.textContent = text;
            timer.classList.toggle("active", active);
        }
        if (revealTimer) {
            revealTimer.textContent = state.weatherGame.currentRound?.resolved
                ? "Click New Duel when you're ready."
                : text;
        }
    }

    function pickWeatherGameCities() {
        const pool = [...WEATHER_GAME_CITIES];
        const firstIndex = Math.floor(Math.random() * pool.length);
        const first = pool.splice(firstIndex, 1)[0];
        const second = pool[Math.floor(Math.random() * pool.length)];
        return [first, second];
    }

    async function buildWeatherGameRound() {
        const round = await api("/api/weather/game/round");
        if (!Array.isArray(round?.cities) || !Array.isArray(round?.weather) || round.cities.length !== 2 || round.weather.length !== 2) {
            throw new Error("Unable to build a saved duel round right now.");
        }
        return {
            cities: round.cities,
            weather: round.weather,
            hotterIndex: Number(round.hotterIndex) === 1 ? 1 : 0,
            guessedIndex: null,
            resolved: false,
        };
    }

    function renderWeatherGameRound() {
        const options = document.getElementById("weatherGameOptions");
        const reveal = document.getElementById("weatherGameReveal");
        if (!options || !reveal) return;

        if (state.weatherGame.loading) {
            options.innerHTML = `<div class="empty-state grid-span-2">Loading two saved city snapshots for a new duel...</div>`;
            reveal.innerHTML = `<div class="empty-state">Saved temperatures are being prepared now.</div>`;
            renderWeatherGameTimer();
            return;
        }

        const round = state.weatherGame.currentRound;
        if (!round) {
            options.innerHTML = `<div class="empty-state grid-span-2">Start a duel to compare saved city temperatures.</div>`;
            reveal.innerHTML = `<div class="empty-state">The result breakdown will appear here after you choose a city.</div>`;
            renderWeatherGameTimer();
            return;
        }

        options.innerHTML = round.cities.map((city, index) => {
            const isCorrect = round.resolved && index === round.hotterIndex;
            const isWrongPick = round.resolved && round.guessedIndex === index && index !== round.hotterIndex;
            const stateClass = isCorrect ? "correct" : isWrongPick ? "wrong" : "";
            return `
                <button type="button" class="weather-game-choice ${stateClass}" data-weather-choice="${index}" ${round.resolved ? "disabled" : ""}>
                    <span class="weather-game-city">${city.name}</span>
                    <span class="weather-game-meta">${city.country}</span>
                    <span class="weather-game-meta">${city.timezone}</span>
                </button>
            `;
        }).join("");

        options.querySelectorAll("[data-weather-choice]").forEach((button) => {
            button.addEventListener("click", () => submitWeatherGuess(Number(button.dataset.weatherChoice)));
        });

        if (!round.resolved) {
            reveal.innerHTML = `<div class="empty-state">Choose the city you think is warmer in this saved snapshot round. Temperatures stay hidden until you guess.</div>`;
            renderWeatherGameTimer();
            return;
        }

        const hotterCity = round.cities[round.hotterIndex];
        const coolerIndex = round.hotterIndex === 0 ? 1 : 0;
        const coolerCity = round.cities[coolerIndex];
        const hotterTemp = round.weather[round.hotterIndex].temperature;
        const coolerTemp = round.weather[coolerIndex].temperature;
        const diff = Math.abs(hotterTemp - coolerTemp).toFixed(1);
        const wasCorrect = round.guessedIndex === round.hotterIndex;

        reveal.innerHTML = `
            <div class="storm-card">
                <div class="eyebrow">${wasCorrect ? "Correct pick" : "Not this time"}</div>
                <h4>${hotterCity.name} was warmer by ${diff}°C</h4>
                ${renderDataLine(hotterCity.name, `${Math.round(hotterTemp)}°C`, getWeatherIconClass(round.weather[round.hotterIndex].weather_code, round.weather[round.hotterIndex].is_day))}
                ${renderDataLine(coolerCity.name, `${Math.round(coolerTemp)}°C`, getWeatherIconClass(round.weather[coolerIndex].weather_code, round.weather[coolerIndex].is_day))}
                <div class="data-line">
                    <span class="data-label-with-icon">
                        <i class="fa-solid fa-cloud-sun weather-inline-icon" aria-hidden="true"></i>
                        <span>Weather</span>
                    </span>
                    <strong class="weather-comparison-value">
                        ${renderWeatherLabel(round.weather[round.hotterIndex])}
                        <span>vs</span>
                        ${renderWeatherLabel(round.weather[coolerIndex])}
                    </strong>
                </div>
                ${renderDataLine("Next duel", `<span id="weatherGameRevealTimer">Click New Duel when you're ready.</span>`)}
            </div>
        `;
        renderWeatherGameTimer();
    }

    async function startWeatherDuel() {
        if (!document.getElementById("weatherGameOptions")) return;
        state.weatherGame.loading = true;
        state.weatherGame.currentRound = null;
        setWeatherGamePrompt("Loading two saved cities for the next duel...");
        renderWeatherGameTimer();
        renderWeatherGameRound();

        try {
            state.weatherGame.currentRound = await buildWeatherGameRound();
            setWeatherGamePrompt("Which city is warmer right now?");
        } catch (error) {
            state.weatherGame.currentRound = null;
            setWeatherGamePrompt("Hot or Cold Duel is unavailable right now.");
            showToast("Hot or Cold Duel", error.message);
        } finally {
            state.weatherGame.loading = false;
            renderWeatherGameRound();
        }
    }

    function submitWeatherGuess(choiceIndex) {
        const round = state.weatherGame.currentRound;
        if (!round || round.resolved) return;

        round.guessedIndex = choiceIndex;
        round.resolved = true;
        state.weatherGame.rounds += 1;

        if (choiceIndex === round.hotterIndex) {
            state.weatherGame.score += 1;
            state.weatherGame.streak += 1;
            setWeatherGamePrompt("Nice read. You picked the warmer city.");
        } else {
            state.weatherGame.streak = 0;
            setWeatherGamePrompt("The other city was warmer this round.");
        }

        persistWeatherGameStats();
        renderWeatherGameStats();
        renderWeatherGameRound();
        renderWeatherGameTimer();
    }

    function setGlobeFocus(title, copy, meta) {
        const titleElement = document.getElementById("globeFocusTitle");
        const copyElement = document.getElementById("globeFocusCopy");
        const metaElement = document.getElementById("globeFocusMeta");
        if (titleElement) titleElement.textContent = title;
        if (copyElement) copyElement.textContent = copy;
        if (metaElement) metaElement.textContent = meta;
    }

    function focusGlobe(latitude, longitude, altitude = 1.45) {
        if (!state.globe || latitude == null || longitude == null) return;
        state.globe.pointOfView({ lat: latitude, lng: longitude, altitude }, 1200);
    }

    function getCountryRadiusMeters(location) {
        const featureCode = normalizeText(location.feature_code);
        if (featureCode === "pcli") return 260000;
        if (featureCode.startsWith("pcl")) return 320000;
        if (featureCode.startsWith("adm")) return 140000;
        return 70000;
    }

    function getDetailMapZoom(location) {
        if (isCountryResult(location)) return 5;
        const featureCode = normalizeText(location.feature_code);
        if (featureCode.startsWith("adm")) return 6;
        return 8;
    }

    function normalizeText(value) {
        return (value || "").trim().toLowerCase();
    }

    function isCountryResult(location) {
        const featureCode = normalizeText(location.feature_code);
        if (featureCode.startsWith("pcl")) return true;
        return normalizeText(location.name) === normalizeText(location.country) && !location.admin1;
    }

    function getLocationAltitude(location) {
        if (isCountryResult(location)) return 0.9;
        const featureCode = normalizeText(location.feature_code);
        if (featureCode.startsWith("adm")) return 0.72;
        return 0.42;
    }

    function choosePrimarySearchResult(results, query) {
        const normalizedQuery = normalizeText(query);
        const exactCountryMatch = results.find((item) => isCountryResult(item) && (
            normalizeText(item.name) === normalizedQuery || normalizeText(item.country) === normalizedQuery
        ));
        if (exactCountryMatch) return exactCountryMatch;

        const exactNameMatch = results.find((item) => normalizeText(item.name) === normalizedQuery);
        if (exactNameMatch) return exactNameMatch;

        return results[0] || null;
    }

    function handleGlobePointClick(point) {
        if (!point) return;
        if (point.kind === "nasa") {
            focusGlobe(point.lat, point.lng, 1.4);
            setGlobeFocus(
                point.title,
                `${point.category || "Live event"} tracked by ${point.source || "NASA EONET"}.`,
                `${formatDate(point.date)}${point.link ? " - Open the NASA event card below for the source link." : ""}`
            );
            return;
        }
        if (point.city) selectCity(point.city);
    }

    function initGlobe() {
        const globeElement = document.getElementById("weatherGlobe");
        if (!globeElement || typeof window.Globe !== "function") {
            setGlobeFocus("Globe unavailable", "The 3D globe library did not load, so live globe mode is not available right now.", "Refresh the page and check your internet connection.");
            return;
        }

        state.globe = window.Globe()(globeElement)
            .globeImageUrl("https://unpkg.com/three-globe/example/img/earth-blue-marble.jpg")
            .bumpImageUrl("https://unpkg.com/three-globe/example/img/earth-topology.png")
            .backgroundColor("rgba(0,0,0,0)")
            .showAtmosphere(true)
            .atmosphereColor("#7fdfff")
            .atmosphereAltitude(0.18)
            .pointLat("lat")
            .pointLng("lng")
            .pointAltitude("altitude")
            .pointRadius("size")
            .pointColor("color")
            .pointLabel("label")
            .pointsMerge(true)
            .onPointClick(handleGlobePointClick);

        const controls = state.globe.controls();
        controls.autoRotate = true;
        controls.autoRotateSpeed = 0.3;
        controls.enablePan = false;
        controls.minDistance = 160;
        controls.maxDistance = 420;
        if (typeof state.globe.renderer === "function") state.globe.renderer().setClearColor(0x000000, 0);

        const resizeGlobe = () => {
            const host = globeElement.parentElement || globeElement;
            state.globe.width(host.clientWidth);
            state.globe.height(host.clientHeight);
        };
        resizeGlobe();
        window.addEventListener("resize", resizeGlobe);
        state.globe.pointOfView(GLOBE_VIEW_WORLD, 0);
    }

    function initDetailMap() {
        const mapElement = document.getElementById("detailMap");
        if (!mapElement || typeof window.L === "undefined") return;

        state.detailMap = window.L.map(mapElement, { zoomControl: true, attributionControl: true }).setView([20, 0], 2);
        window.L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
            attribution: "&copy; OpenStreetMap contributors",
        }).addTo(state.detailMap);
    }

    function updateDetailMapCaption(text) {
        const caption = document.getElementById("detailMapCaption");
        if (caption) caption.textContent = text;
    }

    function scrollToGlobe() {
        const globeStage = document.querySelector(".globe-stage-shell") || document.getElementById("weatherGlobe");
        if (globeStage) {
            globeStage.scrollIntoView({ behavior: "smooth", block: "start" });
        }
    }

    function focusDetailMap(location) {
        if (!state.detailMap || location.latitude == null || location.longitude == null) return;

        if (state.detailMarker) {
            state.detailMap.removeLayer(state.detailMarker);
            state.detailMarker = null;
        }
        if (state.detailCircle) {
            state.detailMap.removeLayer(state.detailCircle);
            state.detailCircle = null;
        }

        const popupLabel = `${location.name}, ${location.country}`;
        state.detailMarker = window.L.marker([location.latitude, location.longitude]).addTo(state.detailMap).bindPopup(popupLabel);

        if (isCountryResult(location)) {
            const radiusMeters = getCountryRadiusMeters(location);
            state.detailCircle = window.L.circle([location.latitude, location.longitude], {
                radius: radiusMeters,
                color: "#64d2ff",
                weight: 1.5,
                fillColor: "#64d2ff",
                fillOpacity: 0.08,
            }).addTo(state.detailMap);
            state.detailMap.setView([location.latitude, location.longitude], getDetailMapZoom(location), { animate: true });
            updateDetailMapCaption(`Country view centered on ${location.name}, now framed closer so city labels are easier to read.`);
        } else {
            state.detailMap.setView([location.latitude, location.longitude], getDetailMapZoom(location), { animate: true });
            updateDetailMapCaption(`Detail map focused on ${location.name}, with labeled streets and nearby places.`);
        }

        state.detailMarker.openPopup();
        setTimeout(() => state.detailMap.invalidateSize(), 120);
    }

    function setNasaStatus(message) {
        const status = document.getElementById("nasaFeedStatus");
        if (status) status.textContent = message;
    }

    function getFilteredNasaEvents() {
        if (state.nasaFilter === "all") return state.nasaEvents;
        const filterMatchers = {
            storms: ["severe storms"],
            floods: ["floods"],
            wildfires: ["wildfires"],
            extremes: ["temperature extremes", "drought", "dust and haze"],
            volcanoes: ["volcanoes"],
        };
        const matchers = filterMatchers[state.nasaFilter] || [];
        return state.nasaEvents.filter((event) => matchers.some((matcher) => (event.category || "").toLowerCase().includes(matcher)));
    }

    function updateNasaFilterButtons() {
        document.querySelectorAll("[data-nasa-filter]").forEach((button) => {
            button.classList.toggle("active", button.dataset.nasaFilter === state.nasaFilter);
        });
    }

    function buildGlobePoints() {
        const points = [];
        state.watchlist.slice(0, 12).forEach((location) => {
            points.push({
                kind: "watchlist",
                lat: location.latitude,
                lng: location.longitude,
                altitude: 0.08,
                size: 0.28,
                color: "#f0c27b",
                label: `<strong>${location.nickname || location.city_name}</strong><br>Saved location`,
                city: { name: location.city_name, country: location.country_name, latitude: location.latitude, longitude: location.longitude, timezone: location.timezone },
            });
        });
        getFilteredNasaEvents().slice(0, 120).forEach((event) => {
            if (event.latitude == null || event.longitude == null) return;
            points.push({
                kind: "nasa",
                lat: event.latitude,
                lng: event.longitude,
                altitude: 0.14,
                size: 0.22,
                color: "#ff7b54",
                label: `<strong>${event.title}</strong><br>${event.category || "NASA event"}`,
                title: event.title,
                category: event.category,
                source: event.source,
                date: event.date,
                link: event.link,
            });
        });
        if (state.selectedCity) {
            points.push({
                kind: "selected-city",
                lat: state.selectedCity.latitude,
                lng: state.selectedCity.longitude,
                altitude: 0.18,
                size: 0.34,
                color: "#64d2ff",
                label: `<strong>${state.selectedCity.name}, ${state.selectedCity.country}</strong><br>Selected location`,
                city: state.selectedCity,
            });
        }
        return points;
    }

    function refreshGlobe() {
        if (state.globe) state.globe.pointsData(buildGlobePoints());
    }

    function buildWeatherCacheKey(city) {
        const latitude = Number(city?.latitude);
        const longitude = Number(city?.longitude);
        if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) return "";
        return [
            latitude.toFixed(4),
            longitude.toFixed(4),
            city?.timezone || "auto",
        ].join(":");
    }

    function readWeatherCache(cache, key, ttlMs) {
        const cached = cache.get(key);
        if (!cached) return null;
        if ((Date.now() - cached.timestamp) > ttlMs) {
            cache.delete(key);
            return null;
        }
        return cached.value;
    }

    function writeWeatherCache(cache, key, value) {
        cache.set(key, { value, timestamp: Date.now() });
        if (cache.size <= WEATHER_CLIENT_CACHE_LIMIT) return;
        const oldestKey = cache.keys().next().value;
        if (oldestKey !== undefined) cache.delete(oldestKey);
    }

    function buildWeatherApiUrl(path, city) {
        return `${path}?latitude=${city.latitude}&longitude=${city.longitude}&timezone=${encodeURIComponent(city.timezone || "auto")}`;
    }

    function delay(ms) {
        return new Promise((resolve) => {
            window.setTimeout(resolve, ms);
        });
    }

    function enqueueWeatherLookup(task) {
        const run = async () => {
            try {
                return await task();
            } finally {
                await delay(WEATHER_LOOKUP_SPACING_MS);
            }
        };
        const scheduled = weatherLookupQueue.then(run, run);
        weatherLookupQueue = scheduled.catch(() => undefined).then(() => undefined);
        return scheduled;
    }

    async function searchCity(query) {
        const response = await api(`/api/weather/search?q=${encodeURIComponent(query)}`);
        return response.results || [];
    }

    async function loadCurrentWeather(city, options = {}) {
        const cacheKey = buildWeatherCacheKey(city);
        if (cacheKey && !options.forceRefresh) {
            const cached = readWeatherCache(weatherResponseCache.current, cacheKey, WEATHER_CURRENT_CACHE_TTL_MS);
            if (cached) return cached;
        }

        const response = await enqueueWeatherLookup(() => api(buildWeatherApiUrl("/api/weather/current", city)));
        if (cacheKey) writeWeatherCache(weatherResponseCache.current, cacheKey, response);
        return response;
    }

    async function loadCurrentWeatherBatch(cities, options = {}) {
        const results = new Array(cities.length).fill(null);
        const uncachedCities = [];
        const uncachedIndices = [];

        cities.forEach((city, index) => {
            const cacheKey = buildWeatherCacheKey(city);
            if (cacheKey && !options.forceRefresh) {
                const cached = readWeatherCache(weatherResponseCache.current, cacheKey, WEATHER_CURRENT_CACHE_TTL_MS);
                if (cached) {
                    results[index] = cached;
                    return;
                }
            }

            uncachedCities.push({
                latitude: city.latitude,
                longitude: city.longitude,
                timezone: city.timezone || "auto",
            });
            uncachedIndices.push(index);
        });

        if (!uncachedCities.length) return results;

        const response = await api("/api/weather/current/batch", {
            method: "POST",
            body: JSON.stringify({ locations: uncachedCities }),
        });
        const batchedResults = Array.isArray(response?.results) ? response.results : [];

        uncachedIndices.forEach((resultIndex, offset) => {
            const weather = batchedResults[offset] || null;
            results[resultIndex] = weather;
            const cacheKey = buildWeatherCacheKey(cities[resultIndex]);
            if (cacheKey && weather) writeWeatherCache(weatherResponseCache.current, cacheKey, weather);
        });

        return results;
    }

    async function loadForecast(city, options = {}) {
        const cacheKey = buildWeatherCacheKey(city);
        if (cacheKey && !options.forceRefresh) {
            const cached = readWeatherCache(weatherResponseCache.forecast, cacheKey, WEATHER_FORECAST_CACHE_TTL_MS);
            if (cached) return cached;
        }

        const response = await enqueueWeatherLookup(() => api(buildWeatherApiUrl("/api/weather/forecast", city)));
        if (cacheKey) writeWeatherCache(weatherResponseCache.forecast, cacheKey, response);
        return response;
    }

    function renderSearchResults(results) {
        const container = document.getElementById("searchResults");
        if (!container) return;
        if (!results.length) {
            container.innerHTML = `<div class="empty-state">No matching cities were found. Try a broader search.</div>`;
            return;
        }
        container.innerHTML = results.map((city, index) => `
            <button type="button" class="search-pill" data-city-index="${index}">
                ${city.name}, ${city.country}${city.admin1 ? ` (${city.admin1})` : ""}${isCountryResult(city) ? " - country" : ""}
            </button>
        `).join("");
        container.querySelectorAll("[data-city-index]").forEach((button) => {
            button.addEventListener("click", () => selectCity(results[Number(button.dataset.cityIndex)]));
        });
    }

    function renderSelectedCity(city) {
        const card = document.getElementById("selectedCityCard");
        if (!card) return;
        card.innerHTML = `
            <div class="storm-card">
                <h4>${city.name}, ${city.country}</h4>
                <div class="data-line"><span>Result type</span><strong>${isCountryResult(city) ? "Country" : "Place"}</strong></div>
                <div class="data-line"><span>Region</span><strong>${city.admin1 || "Not provided"}</strong></div>
                <div class="data-line"><span>Timezone</span><strong>${city.timezone || "auto"}</strong></div>
                <div class="data-line"><span>Coordinates</span><strong>${city.latitude.toFixed(2)}, ${city.longitude.toFixed(2)}</strong></div>
            </div>
        `;
    }

    function renderCurrentWeather(weather) {
        const panel = document.getElementById("currentWeatherPanel");
        if (!panel) return;
        panel.innerHTML = `
            <div class="storm-card weather-condition-card">
                <div class="weather-card-top">
                    ${renderWeatherIcon(weather.weather_code, weather.is_day)}
                    <div class="weather-card-heading">
                        <h4>${weather.weather_label}</h4>
                        <div class="metric-value">${Math.round(weather.temperature)}°C</div>
                    </div>
                </div>
                ${renderDataLine("Feels like", `${Math.round(weather.apparent_temperature)}°C`, "fa-solid fa-temperature-half")}
                ${renderDataLine("Humidity", `${weather.humidity}%`, "fa-solid fa-droplet")}
                ${renderDataLine("Wind", `${weather.wind_speed} km/h`, "fa-solid fa-wind")}
                ${renderDataLine("Precipitation", `${weather.precipitation} mm`, "fa-solid fa-cloud-rain")}
                ${renderDataLine("Local time", weather.local_time || "Unavailable", weather.is_day ? "fa-solid fa-sun" : "fa-solid fa-moon")}
            </div>
        `;
    }

    function renderForecast(forecast) {
        const grid = document.getElementById("forecastGrid");
        if (!grid) return;
        const items = forecast.forecast || [];
        if (!items.length) {
            grid.innerHTML = `<div class="empty-state">Forecast data is not available right now.</div>`;
            return;
        }
        grid.innerHTML = items.map((day) => `
            <article class="forecast-card">
                <div class="forecast-card-top">
                    <div>
                        <div class="eyebrow">${formatDate(day.date)}</div>
                        <h4>${day.weather_label}</h4>
                    </div>
                    ${renderWeatherIcon(day.weather_code, true, "weather-icon-badge weather-icon-badge-compact")}
                </div>
                ${renderDataLine("High", `${Math.round(day.temperature_max)}°C`, "fa-solid fa-temperature-high")}
                ${renderDataLine("Low", `${Math.round(day.temperature_min)}°C`, "fa-solid fa-temperature-low")}
                ${renderDataLine("Rain chance", `${day.precipitation_probability ?? 0}%`, "fa-solid fa-cloud-rain")}
            </article>
        `).join("");
    }

    async function selectCity(city) {
        state.selectedCity = city;
        renderSelectedCity(city);
        refreshGlobe();
        focusGlobe(city.latitude, city.longitude, getLocationAltitude(city));
        focusDetailMap(city);
        setGlobeFocus(
            `${city.name}, ${city.country}`,
            isCountryResult(city)
                ? "Country-level match selected. The globe is framing the country more broadly instead of diving straight into a city view."
                : "Live weather and forecast are loading for this location. Saved places stay pinned on the globe for quick comparisons.",
            `${city.admin1 || "Region not provided"} - ${city.latitude.toFixed(2)}, ${city.longitude.toFixed(2)}`
        );
        try {
            const [currentWeather, forecast] = await Promise.all([loadCurrentWeather(city), loadForecast(city)]);
            renderCurrentWeather(currentWeather);
            renderForecast(forecast);
            setGlobeFocus(`${city.name}, ${city.country}`, `${currentWeather.weather_label} right now with ${Math.round(currentWeather.temperature)}°C and ${currentWeather.wind_speed} km/h winds.`, `${city.timezone || "auto"} - ${formatDate(currentWeather.local_time || "")}`);
        } catch (error) {
            showToast("Weather lookup", error.message);
        }
    }

    async function handleSearchSubmit(event) {
        event.preventDefault();
        const input = document.getElementById("citySearch");
        if (!input) return;
        try {
            const query = input.value.trim();
            const results = await searchCity(query);
            renderSearchResults(results);
            if (results.length === 1) {
                await selectCity(results[0]);
            }
        } catch (error) {
            showToast("Search failed", error.message);
        }
    }

    async function saveSelectedCity(event) {
        event.preventDefault();
        if (!state.selectedCity) {
            showToast("Save city", "Select a city first.");
            return;
        }
        const nickname = document.getElementById("locationNickname").value.trim();
        const priority = Number(document.getElementById("locationPriority").value);
        try {
            await api("/api/watchlist", {
                method: "POST",
                body: JSON.stringify({
                    city_name: state.selectedCity.name,
                    country_name: state.selectedCity.country,
                    latitude: state.selectedCity.latitude,
                    longitude: state.selectedCity.longitude,
                    timezone: state.selectedCity.timezone || "auto",
                    nickname: nickname || null,
                    priority,
                }),
            });
            document.getElementById("saveLocationForm").reset();
            document.getElementById("locationPriority").value = "3";
            showToast("Watchlist updated", "City saved to your watchlist.");
            await loadWatchlist();
        } catch (error) {
            showToast("Save failed", error.message);
        }
    }

    function renderWatchlist(items) {
        const container = document.getElementById("watchlistContainer");
        if (!container) return;
        if (!items.length) {
            container.innerHTML = `<div class="empty-state">Your watchlist is empty right now.</div>`;
            return;
        }
        container.innerHTML = items.map((item) => `
            <form class="watchlist-card watchlist-form" data-location-id="${item.id}">
                <div class="panel-header">
                    <div>
                        <h4>${item.nickname || item.city_name}</h4>
                        <div class="text-muted">${item.city_name}, ${item.country_name}</div>
                    </div>
                    <button type="button" class="btn btn-storm-secondary watchlist-delete watchlist-delete-danger">Remove</button>
                </div>
                <div class="storm-form-grid">
                    <div>
                        <label class="form-label">Nickname</label>
                        <input class="form-control storm-input watchlist-nickname" value="${item.nickname || ""}">
                    </div>
                    <div>
                        <label class="form-label">Priority</label>
                        <select class="form-select storm-input watchlist-priority">
                            ${[1, 2, 3, 4, 5].map((value) => `<option value="${value}" ${item.priority === value ? "selected" : ""}>${value}</option>`).join("")}
                        </select>
                    </div>
                </div>
                <div class="button-row mt-3">
                    <button type="submit" class="btn btn-storm-primary">Save changes</button>
                    <button type="button" class="btn btn-storm-secondary watchlist-open-city">Open on globe</button>
                </div>
            </form>
        `).join("");

        container.querySelectorAll(".watchlist-form").forEach((form) => {
            form.addEventListener("submit", async (submitEvent) => {
                submitEvent.preventDefault();
                const locationId = form.dataset.locationId;
                try {
                    await api(`/api/watchlist/${locationId}`, {
                        method: "PATCH",
                        body: JSON.stringify({
                            nickname: form.querySelector(".watchlist-nickname").value.trim() || null,
                            priority: Number(form.querySelector(".watchlist-priority").value),
                        }),
                    });
                    showToast("Watchlist updated", "Saved city updated.");
                    await loadWatchlist();
                } catch (error) {
                    showToast("Update failed", error.message);
                }
            });

            form.querySelector(".watchlist-delete").addEventListener("click", async () => {
                const locationId = form.dataset.locationId;
                try {
                    await api(`/api/watchlist/${locationId}`, { method: "DELETE" });
                    showToast("Watchlist updated", "Saved city removed.");
                    await loadWatchlist();
                } catch (error) {
                    showToast("Delete failed", error.message);
                }
            });

            form.querySelector(".watchlist-open-city").addEventListener("click", async () => {
                const item = state.watchlist.find((location) => String(location.id) === form.dataset.locationId);
                if (!item) return;
                await selectCity({ name: item.city_name, country: item.country_name, latitude: item.latitude, longitude: item.longitude, timezone: item.timezone });
                scrollToGlobe();
            });
        });
    }

    async function renderWatchlistSnapshots() {
        const container = document.getElementById("watchlistSnapshot");
        if (!container) return;
        if (!state.watchlist.length) {
            container.innerHTML = `<div class="empty-state">Save cities from the explorer to populate your weather dashboard.</div>`;
            return;
        }

        const cities = [...state.watchlist]
            .sort((left, right) => Number(left.priority || 0) - Number(right.priority || 0))
            .slice(0, WATCHLIST_SNAPSHOT_LIMIT);
        const hiddenCityCount = Math.max(0, state.watchlist.length - cities.length);
        const hasInlineWeatherDetails = Boolean(document.getElementById("currentWeatherPanel") && document.getElementById("forecastGrid"));
        const canOpenWeatherDetails = hasInlineWeatherDetails || window.location.pathname === "/app";

        const weatherCards = cities.map((city, index) => {
            const interactionAttrs = canOpenWeatherDetails
                ? ` class="storm-card watchlist-snapshot-card" data-snapshot-index="${index}" role="button" tabindex="0"`
                : ` class="storm-card"`;

            return `
                <article${interactionAttrs}>
                    <div class="weather-snapshot-header">
                        <div>
                            <div class="eyebrow">Priority ${city.priority}</div>
                            <h4>${city.nickname || city.city_name}</h4>
                            <div class="weather-snapshot-location">${city.city_name}, ${city.country_name}</div>
                        </div>
                        ${renderWeatherIcon(null, true, "weather-icon-badge weather-icon-badge-compact")}
                    </div>
                    <div class="metric-value">Saved</div>
                </article>
            `;
        });

        const openSnapshotWeather = async (snapshotIndex) => {
            const city = cities[snapshotIndex];
            if (!city) return;
            const normalizedCity = normalizeExplorerCity({
                name: city.city_name,
                country: city.country_name,
                latitude: city.latitude,
                longitude: city.longitude,
                timezone: city.timezone,
            });
            if (!normalizedCity) return;

            if (hasInlineWeatherDetails) {
                await selectCity(normalizedCity);
                document.getElementById("currentWeatherPanel")?.scrollIntoView({ behavior: "smooth", block: "start" });
                return;
            }

            queuePendingExplorerCity(normalizedCity);
            window.location.href = "/app/explorer#currentWeatherPanel";
        };

        const snapshotNote = `<div class="empty-state">${hiddenCityCount
            ? `Showing your top ${cities.length} saved cities.`
            : "Saved locations are ready."}</div>`;
        container.innerHTML = `${weatherCards.join("")}${snapshotNote}`;

        if (canOpenWeatherDetails) {
            container.querySelectorAll("[data-snapshot-index]").forEach((card) => {
                card.addEventListener("click", async () => {
                    const snapshotIndex = Number(card.dataset.snapshotIndex);
                    if (Number.isNaN(snapshotIndex)) return;
                    await openSnapshotWeather(snapshotIndex);
                });

                card.addEventListener("keydown", async (event) => {
                    if (event.key !== "Enter" && event.key !== " ") return;
                    event.preventDefault();
                    const snapshotIndex = Number(card.dataset.snapshotIndex);
                    if (Number.isNaN(snapshotIndex)) return;
                    await openSnapshotWeather(snapshotIndex);
                });
            });
        }
    }

    async function loadWatchlist() {
        const items = await api("/api/watchlist");
        state.watchlist = items;
        const metricWatchlistCount = document.getElementById("metricWatchlistCount");
        if (metricWatchlistCount) metricWatchlistCount.textContent = items.length;
        renderWatchlist(items);
        await renderWatchlistSnapshots();
        refreshGlobe();
    }

    function renderProfile(user) {
        syncCurrentSessionUser(user);

        const profileSummaryName = document.getElementById("profileSummaryName");
        const profileSummaryEmail = document.getElementById("profileSummaryEmail");
        const profileSummaryRole = document.getElementById("profileSummaryRole");
        const profileSummaryCreated = document.getElementById("profileSummaryCreated");
        const profileUsername = document.getElementById("profileUsername");
        const profileEmail = document.getElementById("profileEmail");
        const deleteAccountUsername = document.getElementById("deleteAccountUsername");

        if (profileSummaryName) profileSummaryName.textContent = user.username || "";
        if (profileSummaryEmail) profileSummaryEmail.textContent = user.email || "";
        if (profileSummaryRole) profileSummaryRole.textContent = formatUserRole(user.role);
        if (profileSummaryCreated) profileSummaryCreated.textContent = formatDateTime(user.created_at);
        if (profileUsername) profileUsername.value = user.username || "";
        if (profileEmail) profileEmail.value = user.email || "";
        if (deleteAccountUsername) deleteAccountUsername.placeholder = `Type ${user.username} exactly`;
    }

    async function loadCurrentUserProfile() {
        const user = await api("/api/users/me");
        renderProfile(user);
    }

    async function handleProfileSubmit(event) {
        event.preventDefault();
        const payload = {
            username: document.getElementById("profileUsername").value.trim(),
            email: document.getElementById("profileEmail").value.trim(),
        };
        const currentPassword = document.getElementById("profileCurrentPassword").value;
        const newPassword = document.getElementById("profileNewPassword").value;

        if (currentPassword || newPassword) {
            payload.current_password = currentPassword;
            payload.new_password = newPassword;
        }

        try {
            const updatedUser = await api("/api/users/me", {
                method: "PATCH",
                body: JSON.stringify(payload),
            });
            document.getElementById("profileCurrentPassword").value = "";
            document.getElementById("profileNewPassword").value = "";
            renderProfile(updatedUser);
            showToast("Profile", "Your account details were updated.");
            if (document.getElementById("adminUserList")) {
                await loadUsers();
            }
        } catch (error) {
            showToast("Profile update", error.message);
        }
    }

    async function handleDeleteAccount(event) {
        event.preventDefault();
        const confirmUsername = document.getElementById("deleteAccountUsername").value.trim();
        const currentPassword = document.getElementById("deleteAccountPassword").value;

        if (!window.confirm("Delete your StormScope account permanently? This cannot be undone.")) {
            return;
        }

        try {
            await api("/api/users/me", {
                method: "DELETE",
                body: JSON.stringify({
                    confirm_username: confirmUsername,
                    current_password: currentPassword,
                }),
            });
            window.location.assign("/login");
        } catch (error) {
            showToast("Delete account", error.message);
        }
    }

    function bindPasswordToggles() {
        document.querySelectorAll("[data-password-toggle]").forEach((button) => {
            if (button.dataset.passwordToggleBound === "true") return;
            const targetId = button.dataset.passwordTarget;
            const input = targetId ? document.getElementById(targetId) : null;
            const icon = button.querySelector(".material-symbols-outlined");
            if (!input || !icon) return;

            const showLabel = button.getAttribute("aria-label") || "Show password";
            const hideLabel = showLabel.replace(/^Show/i, "Hide");

            const syncPasswordToggleState = () => {
                const isVisible = input.type === "text";
                icon.textContent = isVisible ? "visibility_off" : "visibility";
                button.setAttribute("aria-label", isVisible ? hideLabel : showLabel);
                button.setAttribute("aria-pressed", String(isVisible));
            };

            button.addEventListener("click", () => {
                input.type = input.type === "password" ? "text" : "password";
                syncPasswordToggleState();
                input.focus({ preventScroll: true });
            });

            button.dataset.passwordToggleBound = "true";
            syncPasswordToggleState();
        });
    }

    function renderAdminUsers(users) {
        const container = document.getElementById("adminUserList");
        if (!container) return;

        if (!users.length) {
            container.innerHTML = `<div class="empty-state">No user accounts are available.</div>`;
            return;
        }

        const currentUserId = getCurrentSessionUserId();
        container.innerHTML = users.map((user) => {
            const isCurrentUser = user.id === currentUserId;
            return `
                <form class="watchlist-card admin-user-card admin-user-form" data-user-id="${user.id}">
                    <div class="panel-header">
                        <div>
                            <div class="timeline-card-topline">
                                <div class="eyebrow">${escapeHtml(formatUserRole(user.role))}</div>
                                <span class="record-source-badge ${user.role === "admin" ? "admin-user-role-badge-admin" : "admin-user-role-badge-member"}">
                                    ${user.role === "admin" ? "Admin" : "Member"}
                                </span>
                            </div>
                            <h4>${escapeHtml(user.username)}</h4>
                            <div class="admin-user-email-text">${escapeHtml(user.email)}</div>
                        </div>
                        <div class="admin-user-created">Joined ${escapeHtml(formatDate(user.created_at))}</div>
                    </div>
                    <div class="storm-form-grid admin-user-grid">
                        <div>
                            <label class="form-label">Username</label>
                            <input class="form-control storm-input admin-user-username" value="${escapeHtml(user.username)}" ${isCurrentUser ? "disabled" : "required"}>
                        </div>
                        <div>
                            <label class="form-label">Email</label>
                            <input class="form-control storm-input admin-user-email" type="email" value="${escapeHtml(user.email)}" ${isCurrentUser ? "disabled" : "required"}>
                        </div>
                        <div>
                            <label class="form-label">Role</label>
                            <select class="form-select storm-input admin-user-role" ${isCurrentUser ? "disabled" : ""}>
                                <option value="regular_user" ${user.role === "regular_user" ? "selected" : ""}>Regular user</option>
                                <option value="admin" ${user.role === "admin" ? "selected" : ""}>Admin</option>
                            </select>
                        </div>
                    </div>
                    <div class="button-row mt-3">
                        <button type="submit" class="btn btn-storm-primary" ${isCurrentUser ? "disabled" : ""}>Save user</button>
                        <button type="button" class="btn btn-storm-secondary admin-user-delete ${isCurrentUser ? "d-none" : ""}">Delete user</button>
                    </div>
                    <div class="admin-record-note">
                        ${isCurrentUser
                            ? "This is your account. Use the Profile page if you want to update or delete it."
                            : "Update this user's details here, or delete the account if needed."}
                    </div>
                </form>
            `;
        }).join("");

        container.querySelectorAll(".admin-user-form").forEach((form) => {
            form.addEventListener("submit", async (submitEvent) => {
                submitEvent.preventDefault();
                const userId = form.dataset.userId;
                try {
                    await api(`/api/users/${userId}`, {
                        method: "PATCH",
                        body: JSON.stringify({
                            username: form.querySelector(".admin-user-username").value.trim(),
                            email: form.querySelector(".admin-user-email").value.trim(),
                            role: form.querySelector(".admin-user-role").value,
                        }),
                    });
                    showToast("User management", "Account updated.");
                    await loadUsers();
                } catch (error) {
                    showToast("User update", error.message);
                }
            });

            form.querySelector(".admin-user-delete")?.addEventListener("click", async () => {
                const userName = form.querySelector(".admin-user-username").value.trim() || "this user";
                if (!window.confirm(`Delete ${userName}'s account permanently?`)) {
                    return;
                }

                try {
                    await api(`/api/users/${form.dataset.userId}`, { method: "DELETE" });
                    showToast("User management", "Account deleted.");
                    await loadUsers();
                } catch (error) {
                    showToast("User delete", error.message);
                }
            });
        });
    }

    async function loadUsers() {
        const users = await api("/api/users");
        state.users = users;
        renderAdminUsers(users);
    }

    const DEFAULT_DISASTER_CATEGORIES = [
        "Flood",
        "Floods",
        "Severe Storms",
        "Wildfires",
        "Landslides",
        "Volcanoes",
        "Drought",
        "Temperature Extremes",
        "Dust and Haze",
        "Sea and Lake Ice",
    ];

    function isNasaBackedRecord(event) {
        return event?.external_source === "NASA EONET";
    }

    function getRecordKindLabel(event) {
        return isNasaBackedRecord(event) ? "NASA-synced record" : "Manual StormScope record";
    }

    function getRecordLocationText(event) {
        if (event.region && event.country) return `${event.region}, ${event.country}`;
        return event.region || event.country || "Location not specified";
    }

    function getRecordSourceText(event) {
        return isNasaBackedRecord(event)
            ? `${event.source_name} via StormScope sync`
            : (event.source_name || "StormScope Desk");
    }

    function renderDisasters(items, targetId = "disasterList") {
        const container = document.getElementById(targetId);
        if (!container) return;
        if (!items.length) {
            container.innerHTML = `<div class="empty-state">No disaster events matched the current filters.</div>`;
            return;
        }
        container.innerHTML = items.map((event) => `
            <article class="timeline-card">
                <div class="panel-header">
                    <div>
                        <div class="timeline-card-topline">
                            <div class="eyebrow">${event.category} - ${event.severity}</div>
                            <span class="record-source-badge ${isNasaBackedRecord(event) ? "record-source-badge-nasa" : "record-source-badge-manual"}">${getRecordKindLabel(event)}</span>
                        </div>
                        <h4>${event.title}</h4>
                    </div>
                    <div>${formatDate(event.event_date)}</div>
                </div>
                <p>${event.short_summary}</p>
                <div class="data-line"><span>Location</span><strong>${getRecordLocationText(event)}</strong></div>
                <div class="data-line"><span>Source</span><strong>${getRecordSourceText(event)}</strong></div>
                ${isNasaBackedRecord(event) && event.last_synced_at ? `<div class="data-line"><span>Last synced</span><strong>${formatDate(event.last_synced_at)}</strong></div>` : ""}
            </article>
        `).join("");
    }

    function populateDisasterCategoryOptions(items) {
        const select = document.getElementById("filterCategory");
        if (!select) return;

        const currentValue = select.value || "";
        const existingValues = Array.from(select.options)
            .map((option) => option.value)
            .filter(Boolean);
        const categories = Array.from(new Set([
            ...DEFAULT_DISASTER_CATEGORIES,
            ...existingValues,
            ...items.map((item) => item.category).filter(Boolean),
        ])).sort((left, right) => left.localeCompare(right));

        select.innerHTML = "";

        const defaultOption = document.createElement("option");
        defaultOption.value = "";
        defaultOption.textContent = "All categories";
        select.appendChild(defaultOption);

        categories.forEach((category) => {
            const option = document.createElement("option");
            option.value = category;
            option.textContent = category;
            select.appendChild(option);
        });

        select.value = categories.includes(currentValue) ? currentValue : "";
    }

    function populateAdminCategoryOptions(items) {
        const select = document.getElementById("adminCategory");
        const customInput = document.getElementById("adminCategoryCustom");
        if (!select) return;

        const currentValue = select.value || "";
        const currentCustomValue = customInput?.value?.trim() || "";
        const existingValues = Array.from(select.options)
            .map((option) => option.value)
            .filter((value) => value && value !== "Custom");
        const categories = Array.from(new Set([
            ...DEFAULT_DISASTER_CATEGORIES,
            ...existingValues,
            ...items.map((item) => item.category).filter((value) => value && value !== "Custom"),
        ])).sort((left, right) => left.localeCompare(right));

        select.innerHTML = "";

        const defaultOption = document.createElement("option");
        defaultOption.value = "";
        defaultOption.textContent = "Select a category";
        defaultOption.disabled = true;
        defaultOption.hidden = true;
        select.appendChild(defaultOption);

        categories.forEach((category) => {
            const option = document.createElement("option");
            option.value = category;
            option.textContent = category;
            select.appendChild(option);
        });

        const customOption = document.createElement("option");
        customOption.value = "Custom";
        customOption.textContent = "Custom";
        select.appendChild(customOption);

        if (currentValue === "Custom" || (currentCustomValue && !categories.includes(currentValue))) {
            select.value = "Custom";
        } else {
            select.value = categories.includes(currentValue) ? currentValue : "";
        }

        syncAdminCategoryInput();
    }

    function syncAdminCategoryInput(customValue = "") {
        const select = document.getElementById("adminCategory");
        const customInput = document.getElementById("adminCategoryCustom");
        if (!select || !customInput) return;

        const isCustom = select.value === "Custom";
        customInput.classList.toggle("d-none", !isCustom);
        customInput.required = isCustom;

        if (isCustom) {
            if (customValue) {
                customInput.value = customValue;
            }
        } else {
            customInput.value = "";
        }

        window.requestAnimationFrame(syncAdminRecordsPanelHeight);
    }

    function syncAdminRecordsPanelHeight() {
        const grid = document.querySelector(".admin-grid");
        const editorPanel = grid?.querySelector(".storm-panel:not(.admin-records-panel)");
        const recordsPanel = grid?.querySelector(".admin-records-panel");
        const recordsHeader = recordsPanel?.querySelector(".panel-header");
        const recordsList = document.getElementById("adminDisasterList");

        if (!grid || !editorPanel || !recordsPanel || !recordsHeader || !recordsList) return;

        if (window.innerWidth <= 991) {
            recordsPanel.style.height = "";
            recordsList.style.maxHeight = "";
            return;
        }

        const editorHeight = Math.ceil(editorPanel.getBoundingClientRect().height);
        if (!editorHeight) return;

        recordsPanel.style.height = `${editorHeight}px`;

        const panelStyles = window.getComputedStyle(recordsPanel);
        const headerStyles = window.getComputedStyle(recordsHeader);
        const availableHeight = editorHeight
            - parseFloat(panelStyles.paddingTop || "0")
            - parseFloat(panelStyles.paddingBottom || "0")
            - recordsHeader.getBoundingClientRect().height
            - parseFloat(headerStyles.marginBottom || "0");

        recordsList.style.maxHeight = `${Math.max(Math.floor(availableHeight), 220)}px`;
    }

    async function loadDisasters(options = {}) {
        const query = new URLSearchParams();
        if (options.country) query.set("country", options.country);
        if (options.category) query.set("category", options.category);
        if (options.severity) query.set("severity", options.severity);
        const url = query.toString() ? `/api/disasters?${query.toString()}` : "/api/disasters";
        const items = await api(url);
        state.disasters = items;
        const metricDisasterCount = document.getElementById("metricDisasterCount");
        if (metricDisasterCount) metricDisasterCount.textContent = items.length;
        populateDisasterCategoryOptions(items);
        populateAdminCategoryOptions(items);
        renderDisasters(items);
        renderAdminDisasters(items);
    }

    async function handleDisasterFilterSubmit(event) {
        event.preventDefault();
        try {
            await loadDisasters({
                country: document.getElementById("filterCountry").value.trim(),
                category: document.getElementById("filterCategory").value.trim(),
                severity: document.getElementById("filterSeverity").value,
            });
        } catch (error) {
            showToast("Timeline filter", error.message);
        }
    }

    function renderNasaFeed() {
        const container = document.getElementById("nasaFeed");
        const visibleCount = document.getElementById("nasaVisibleCount");
        if (!container) return;
        updateNasaFilterButtons();
        const events = getFilteredNasaEvents();
        if (visibleCount) visibleCount.textContent = events.length;
        if (!events.length) {
            container.innerHTML = `<div class="empty-state">No NASA events match this category right now.</div>`;
            refreshGlobe();
            return;
        }
        container.innerHTML = events.map((event) => `
            <article class="nasa-card">
                <div class="nasa-card-top">
                    <span class="nasa-category-badge">${event.category || "Live event"}</span>
                </div>
                <h4 class="nasa-card-title">${event.title}</h4>
                <div class="nasa-card-copy">
                    ${event.latitude != null && event.longitude != null ? `Mapped at ${event.latitude.toFixed(2)}, ${event.longitude.toFixed(2)}.` : "Coordinates not available for this event."}
                </div>
                <div class="data-line"><span>Source</span><strong>${event.source || "NASA EONET"}</strong></div>
                <div class="data-line"><span>Date</span><strong>${formatDate(event.date)}</strong></div>
                <div class="nasa-card-footer">
                    <span class="text-muted">${event.id || "NASA event"}</span>
                    <a class="nasa-link" href="${event.link}" target="_blank" rel="noopener noreferrer">Open NASA event</a>
                </div>
            </article>
        `).join("");
        refreshGlobe();
    }

    async function loadNasaFeed(showToastOnError = true) {
        try {
            setNasaStatus("Loading worldwide NASA EONET intake...");
            const response = await api("/api/external/eonet/events?limit=60");
            const events = response.events || [];
            state.nasaEvents = events;
            const metricNasaCount = document.getElementById("metricNasaCount");
            if (metricNasaCount) metricNasaCount.textContent = events.length;
            setNasaStatus(`${events.length} live NASA events ready for review or sync.`);
            setGlobeFocus(
                "StormScope live globe",
                "Move between your selected place, personal watchlist, and active event markers without leaving the map.",
                "Saved places and live events wrapped around the globe."
            );
            renderNasaFeed();
        } catch (error) {
            state.nasaEvents = [];
            const metricNasaCount = document.getElementById("metricNasaCount");
            const visibleCount = document.getElementById("nasaVisibleCount");
            if (metricNasaCount) metricNasaCount.textContent = "0";
            if (visibleCount) visibleCount.textContent = "0";
            setNasaStatus("Live NASA intake unavailable right now.");
            renderNasaFeed();
            if (showToastOnError) showToast("NASA feed", error.message);
        }
    }

    async function syncNasaTimeline() {
        try {
            const response = await api("/api/admin/disasters/sync-nasa?limit=250&include_wildfires=true", { method: "POST" });
            showToast("NASA sync", `Imported ${response.imported} and updated ${response.updated} NASA events in StormScope records.`);
            await Promise.all([loadDisasters(), loadNasaFeed(false)]);
        } catch (error) {
            showToast("NASA sync", error.message);
        }
    }

    function setAdminFormState(event = null) {
        const title = document.getElementById("adminFormTitle");
        const hiddenId = document.getElementById("adminEventId");
        const categorySelect = document.getElementById("adminCategory");
        const customCategoryInput = document.getElementById("adminCategoryCustom");
        if (!title || !hiddenId) return;
        const editing = Boolean(event);
        title.textContent = editing ? `Editing: ${event.title}` : "Create a new event";
        hiddenId.value = editing ? event.id : "";
        document.getElementById("adminTitle").value = event?.title || "";
        document.getElementById("adminCountry").value = event?.country || "";
        document.getElementById("adminRegion").value = event?.region || "";
        const categoryValue = event?.category || "";
        const availableCategories = categorySelect
            ? Array.from(categorySelect.options).map((option) => option.value)
            : [];
        if (categorySelect) {
            if (categoryValue && availableCategories.includes(categoryValue)) {
                categorySelect.value = categoryValue;
                syncAdminCategoryInput();
            } else if (categoryValue) {
                categorySelect.value = "Custom";
                syncAdminCategoryInput(categoryValue);
            } else {
                categorySelect.value = "";
                if (customCategoryInput) customCategoryInput.value = "";
                syncAdminCategoryInput();
            }
        }
        document.getElementById("adminEventDate").value = event?.event_date || "";
        document.getElementById("adminSeverity").value = event?.severity || "Moderate";
        document.getElementById("adminSummary").value = event?.short_summary || "";
        document.getElementById("adminLatitude").value = event?.latitude ?? "";
        document.getElementById("adminLongitude").value = event?.longitude ?? "";
        document.getElementById("adminSourceName").value = event?.source_name || "StormScope Desk";
        document.getElementById("adminSourceUrl").value = event?.source_url || "";
        window.requestAnimationFrame(syncAdminRecordsPanelHeight);
    }

    function renderAdminDisasters(items) {
        const container = document.getElementById("adminDisasterList");
        if (!container) return;
        if (!items.length) {
            container.innerHTML = `<div class="empty-state">No disaster records are available.</div>`;
            window.requestAnimationFrame(syncAdminRecordsPanelHeight);
            return;
        }
        container.innerHTML = items.map((event) => `
            <article class="timeline-card">
                <div class="panel-header">
                    <div>
                        <div class="timeline-card-topline">
                            <div class="eyebrow">${event.category} - ${event.severity}</div>
                            <span class="record-source-badge ${isNasaBackedRecord(event) ? "record-source-badge-nasa" : "record-source-badge-manual"}">${getRecordKindLabel(event)}</span>
                        </div>
                        <h4>${event.title}</h4>
                    </div>
                    <div>${formatDate(event.event_date)}</div>
                </div>
                <p>${event.short_summary}</p>
                <div class="data-line"><span>Location</span><strong>${getRecordLocationText(event)}</strong></div>
                <div class="data-line"><span>Source</span><strong>${getRecordSourceText(event)}</strong></div>
                <div class="button-row">
                    ${isNasaBackedRecord(event)
                        ? ``
                        : `
                            <button class="btn btn-storm-primary admin-edit" data-event-id="${event.id}" type="button">Edit</button>
                            <button class="btn btn-storm-secondary admin-delete" data-event-id="${event.id}" type="button">Delete</button>
                        `}
                </div>
            </article>
        `).join("");

        container.querySelectorAll(".admin-edit").forEach((button) => {
            button.addEventListener("click", () => {
                const event = state.disasters.find((item) => item.id === Number(button.dataset.eventId));
                setAdminFormState(event);
                window.scrollTo({ top: 0, behavior: "smooth" });
            });
        });

        container.querySelectorAll(".admin-delete").forEach((button) => {
            button.addEventListener("click", async () => {
                try {
                    await api(`/api/admin/disasters/${button.dataset.eventId}`, { method: "DELETE" });
                    showToast("Disaster desk", "Event deleted.");
                    await loadDisasters();
                } catch (error) {
                    showToast("Delete failed", error.message);
                }
            });
        });

        window.requestAnimationFrame(syncAdminRecordsPanelHeight);
    }

    async function handleAdminSubmit(event) {
        event.preventDefault();
        const eventId = document.getElementById("adminEventId").value;
        const selectedCategory = document.getElementById("adminCategory").value;
        const customCategory = document.getElementById("adminCategoryCustom").value.trim();
        const category = selectedCategory === "Custom" ? customCategory : selectedCategory;
        const payload = {
            title: document.getElementById("adminTitle").value.trim(),
            country: document.getElementById("adminCountry").value.trim(),
            region: document.getElementById("adminRegion").value.trim() || null,
            category,
            event_date: document.getElementById("adminEventDate").value,
            severity: document.getElementById("adminSeverity").value,
            short_summary: document.getElementById("adminSummary").value.trim(),
            latitude: document.getElementById("adminLatitude").value ? Number(document.getElementById("adminLatitude").value) : null,
            longitude: document.getElementById("adminLongitude").value ? Number(document.getElementById("adminLongitude").value) : null,
            source_name: document.getElementById("adminSourceName").value.trim(),
            source_url: document.getElementById("adminSourceUrl").value.trim() || null,
        };
        try {
            if (eventId) {
                await api(`/api/admin/disasters/${eventId}`, { method: "PATCH", body: JSON.stringify(payload) });
                showToast("Disaster desk", "Event updated.");
            } else {
                await api("/api/admin/disasters", { method: "POST", body: JSON.stringify(payload) });
                showToast("Disaster desk", "Event created.");
            }
            setAdminFormState();
            document.getElementById("adminDisasterForm").reset();
            document.getElementById("adminSourceName").value = "StormScope Desk";
            document.getElementById("adminSeverity").value = "Moderate";
            await loadDisasters();
        } catch (error) {
            showToast("Save failed", error.message);
        }
    }

    function bindEvents() {
        document.getElementById("mobileNavToggle")?.addEventListener("click", toggleMobileNav);
        document.getElementById("mobileNavClose")?.addEventListener("click", closeMobileNav);
        document.getElementById("mobileNavBackdrop")?.addEventListener("click", closeMobileNav);
        document.getElementById("stormscopeLogoTrigger")?.addEventListener("click", openLogoModal);
        document.getElementById("stormscopeLogoModalClose")?.addEventListener("click", closeLogoModal);
        document.getElementById("stormscopeLogoModal")?.addEventListener("click", (event) => {
            if (event.target === event.currentTarget) {
                closeLogoModal();
            }
        });
        bindPasswordToggles();
        document.querySelectorAll("#stormscopeSidebarNav a, .logout-link").forEach((link) => {
            link.addEventListener("click", () => {
                closeMobileNav();
            });
        });
        document.getElementById("weatherSearchForm")?.addEventListener("submit", handleSearchSubmit);
        document.getElementById("saveLocationForm")?.addEventListener("submit", saveSelectedCity);
        document.getElementById("profileForm")?.addEventListener("submit", handleProfileSubmit);
        document.getElementById("deleteAccountForm")?.addEventListener("submit", handleDeleteAccount);
        document.getElementById("newWeatherDuel")?.addEventListener("click", startWeatherDuel);
        document.getElementById("disasterFilterForm")?.addEventListener("submit", handleDisasterFilterSubmit);
        document.getElementById("loadNasaOverlay")?.addEventListener("click", () => {
            focusGlobe(GLOBE_VIEW_WORLD.lat, GLOBE_VIEW_WORLD.lng, GLOBE_VIEW_WORLD.altitude);
            loadNasaFeed();
        });
        document.getElementById("refreshNasaFeed")?.addEventListener("click", loadNasaFeed);
        document.getElementById("syncNasaTimeline")?.addEventListener("click", syncNasaTimeline);
        document.getElementById("adminCategory")?.addEventListener("change", () => syncAdminCategoryInput());
        window.addEventListener("resize", syncAdminRecordsPanelHeight);
        window.addEventListener("resize", syncMobileNavForViewport);
        document.addEventListener("keydown", (event) => {
            if (event.key === "Escape") {
                if (document.body?.classList.contains("stormscope-logo-modal-open")) {
                    closeLogoModal();
                    return;
                }
                closeMobileNav();
            }
        });
        document.querySelectorAll("[data-nasa-filter]").forEach((button) => {
            button.addEventListener("click", () => {
                state.nasaFilter = button.dataset.nasaFilter || "all";
                renderNasaFeed();
            });
        });
        document.getElementById("adminDisasterForm")?.addEventListener("submit", handleAdminSubmit);
        document.getElementById("adminCancelEdit")?.addEventListener("click", () => {
            document.getElementById("adminDisasterForm")?.reset();
            document.getElementById("adminSourceName").value = "StormScope Desk";
            document.getElementById("adminSeverity").value = "Moderate";
            syncAdminCategoryInput();
            setAdminFormState();
        });
    }

    async function init() {
        loadWeatherGameStats();
        renderWeatherGameStats();
        renderWeatherGameRound();
        renderWeatherGameTimer();
        initGlobe();
        initDetailMap();
        bindEvents();
        syncMobileNavForViewport();

        if (
            document.getElementById("watchlistContainer")
            || document.getElementById("watchlistSnapshot")
            || document.getElementById("metricWatchlistCount")
        ) {
            try {
                await loadWatchlist();
            } catch (error) {
                showToast("Watchlist", error.message);
            }
        }

        if (
            document.getElementById("profileForm")
            || document.getElementById("profileSummaryName")
        ) {
            try {
                await loadCurrentUserProfile();
            } catch (error) {
                showToast("Profile", error.message);
            }
        }

        if (
            document.getElementById("disasterList")
            || document.getElementById("metricDisasterCount")
            || document.getElementById("adminDisasterList")
        ) {
            try {
                await loadDisasters();
            } catch (error) {
                showToast("Timeline", error.message);
            }
        }

        if (document.getElementById("adminUserList")) {
            try {
                await loadUsers();
            } catch (error) {
                showToast("User management", error.message);
            }
        }

        if (
            document.getElementById("nasaFeed")
            || document.getElementById("nasaFeedStatus")
            || document.getElementById("metricNasaCount")
            || document.getElementById("weatherGlobe")
        ) {
            try {
                await loadNasaFeed(false);
            } catch (error) {
                
            }
        }

        refreshGlobe();
        if (document.getElementById("adminDisasterForm")) {
            setAdminFormState();
            document.getElementById("adminSourceName").value = "StormScope Desk";
        }
        if (document.getElementById("currentWeatherPanel") && document.getElementById("forecastGrid")) {
            const pendingCity = consumePendingExplorerCity();
            if (pendingCity) {
                try {
                    await selectCity(pendingCity);
                    document.getElementById("currentWeatherPanel")?.scrollIntoView({ behavior: "smooth", block: "start" });
                } catch (error) {
                    showToast("Weather details", error.message);
                }
            }
        }
    }

    return { init };
})();

document.addEventListener("DOMContentLoaded", StormScopeApp.init);
