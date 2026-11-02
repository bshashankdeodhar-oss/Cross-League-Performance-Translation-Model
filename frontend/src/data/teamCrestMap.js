/**
 * CLPTM Team Crest Mapping
 *
 * Maps dataset team names (from feature_dataset.csv / FBRef) to ESPN CDN logo URLs.
 * Uses ESPN's dark-mode logos (white-on-transparent) which blend perfectly with the
 * CRT terminal aesthetic.
 *
 * Logo URL pattern: https://a.espncdn.com/i/teamlogos/soccer/500-dark/{espn_id}.png
 * Fallback (light): https://a.espncdn.com/i/teamlogos/soccer/500/{espn_id}.png
 */

const ESPN_CDN_BASE = 'https://a.espncdn.com/i/teamlogos/soccer/500-dark';
const ESPN_CDN_LIGHT = 'https://a.espncdn.com/i/teamlogos/soccer/500';

/**
 * Primary mapping: dataset team name → ESPN team ID.
 * Verified directly against ESPN soccer database.
 */
export const TEAM_ESPN_IDS = {
  // ── Premier League ───────────────────────────────────────────────────
  'Arsenal': 359,
  'Aston Villa': 362,
  'Bournemouth': 349,
  'Brentford': 337,
  'Brighton': 331,
  'Burnley': 379,
  'Cardiff City': 427,
  'Chelsea': 363,
  'Crystal Palace': 384,
  'Everton': 368,
  'Fulham': 370,
  'Huddersfield': 380,
  'Ipswich Town': 373,
  'Leeds United': 357,
  'Leicester City': 375,
  'Liverpool': 364,
  'Luton Town': 301,
  'Manchester City': 382,
  'Manchester Utd': 360,
  'Newcastle Utd': 361,
  "Nott'ham Forest": 393,
  'Norwich City': 381,
  'Sheffield Utd': 398,
  'Southampton': 376,
  'Stoke City': 336,
  'Swansea City': 318,
  'Tottenham': 367,
  'Watford': 395,
  'West Brom': 383,
  'West Ham': 371,
  'Wolves': 380,

  // ── Bundesliga ───────────────────────────────────────────────────────
  'Arminia': 10517,
  'Augsburg': 3841,
  'Bayern Munich': 132,
  'Bochum': 121,
  'Dortmund': 124,
  'Düsseldorf': 166,
  'Eint Frankfurt': 125,
  'Freiburg': 126,
  'Gladbach': 268,
  "M'Gladbach": 268,
  'Greuther Fürth': 2985,
  'Hamburger SV': 127,
  'Hannover 96': 136,
  'Heidenheim': 6418,
  'Hertha BSC': 267,
  'Hoffenheim': 7911,
  'Holstein Kiel': 7884,
  'Köln': 122,
  'Leverkusen': 131,
  'Mainz 05': 2950,
  'Nürnberg': 129,
  'Paderborn 07': 3307,
  'RB Leipzig': 11420,
  'Schalke 04': 133,
  'St. Pauli': 270,
  'Stuttgart': 134,
  'Union Berlin': 598,
  'Werder Bremen': 137,
  'Wolfsburg': 138,
  'Darmstadt 98': 2966,

  // ── La Liga ──────────────────────────────────────────────────────────
  'Alavés': 96,
  'Almería': 3803,
  'Athletic Club': 93,
  'Atlético Madrid': 1068,
  'Barcelona': 83,
  'Betis': 244,
  'Cádiz': 3842,
  'Celta Vigo': 85,
  'Eibar': 3731,
  'Elche': 3751,
  'Espanyol': 88,
  'Getafe': 2922,
  'Girona': 9812,
  'Granada': 3747,
  'Huesca': 3856,
  'La Coruña': 90,
  'Las Palmas': 98,
  'Leganés': 17534,
  'Levante': 1538,
  'Mallorca': 84,
  'Málaga': 99,
  'Osasuna': 97,
  'Rayo Vallecano': 101,
  'Real Madrid': 86,
  'Real Sociedad': 89,
  'Sevilla': 243,
  'Valencia': 94,
  'Valladolid': 95,
  'Villarreal': 102,

  // ── Serie A ──────────────────────────────────────────────────────────
  'Atalanta': 105,
  'Benevento': 7183,
  'Bologna': 107,
  'Brescia': 155,
  'Cagliari': 2925,
  'Chievo': 3438,
  'Como': 2572,
  'Cremonese': 3449,
  'Crotone': 10258,
  'Empoli': 2574,
  'Fiorentina': 109,
  'Frosinone': 4057,
  'Genoa': 3263,
  'Hellas Verona': 119,
  'Inter': 110,
  'Juventus': 111,
  'Lazio': 112,
  'Lecce': 113,
  'Milan': 103,
  'Monza': 4007,
  'Napoli': 114,
  'Parma': 115,
  'Roma': 104,
  'SPAL': 3630,
  'Salernitana': 3617,
  'Sampdoria': 116,
  'Sassuolo': 3997,
  'Spezia': 3632,
  'Torino': 239,
  'Udinese': 118,
  'Venezia': 17530,

  // ── Ligue 1 ──────────────────────────────────────────────────────────
  'Ajaccio': 159,
  'Amiens': 3786,
  'Angers': 7868,
  'Auxerre': 172,
  'Bordeaux': 1816,
  'Brest': 6997,
  'Caen': 1817,
  'Clermont Foot': 3778,
  'Dijon': 3750,
  'Guingamp': 3773,
  'Le Havre': 3236,
  'Lens': 175,
  'Lille': 166,
  'Lorient': 273,
  'Lyon': 167,
  'Marseille': 176,
  'Metz': 3779,
  'Monaco': 174,
  'Montpellier': 274,
  'Nantes': 165,
  'Nice': 2502,
  'Nîmes': 3777,
  'Paris S-G': 160,
  'Paris FC': 3244,
  'Pau': 19307,
  'Reims': 3243,
  'Rennes': 169,
  'Saint-Étienne': 178,
  'Strasbourg': 180,
  'Toulouse': 179,
  'Troyes': 170,

  // ── Other European / Active Clubs (2026/27 Transfers) ─────────────────
  'Sunderland': 366,
  'Queens Park Rangers': 334,
  '1. FC Kaiserslautern': 127,
  '1. FC Nürnberg': 131,
  'Oviedo': 97,
  'Real Oviedo': 97,
  'Athletic Bilbao': 93,
  'Pisa': 2697,
  'Anderlecht': 215,
  'Braga': 2465,
  'Celtic': 243,
  'Cruzeiro': 3454,
  'Estrela da Amadora': 10565,
  'Rangers': 244,
  'Red Bull Salzburg': 536,
  'Slavia Prague': 489,
  'Sporting CP': 282,
  'Sporting Lisbon': 282,
  'Westerlo': 2392,
  'Zira': 18047,
};

/**
 * Team to Canonical League Mapping
 */
export const TEAM_LEAGUE_MAP = {
  // Premier League
  'Arsenal': 'Premier League',
  'Aston Villa': 'Premier League',
  'Bournemouth': 'Premier League',
  'Brentford': 'Premier League',
  'Brighton': 'Premier League',
  'Burnley': 'Premier League',
  'Chelsea': 'Premier League',
  'Crystal Palace': 'Premier League',
  'Everton': 'Premier League',
  'Fulham': 'Premier League',
  'Ipswich Town': 'Premier League',
  'Leeds United': 'Premier League',
  'Leicester City': 'Premier League',
  'Liverpool': 'Premier League',
  'Luton Town': 'Premier League',
  'Manchester City': 'Premier League',
  'Manchester Utd': 'Premier League',
  'Newcastle Utd': 'Premier League',
  "Nott'ham Forest": 'Premier League',
  'Sheffield Utd': 'Premier League',
  'Southampton': 'Premier League',
  'Tottenham': 'Premier League',
  'West Ham': 'Premier League',
  'Wolves': 'Premier League',

  // Bundesliga
  'Bayern Munich': 'Bundesliga',
  'Leverkusen': 'Bundesliga',
  'Dortmund': 'Bundesliga',
  'RB Leipzig': 'Bundesliga',
  'Eint Frankfurt': 'Bundesliga',
  'Stuttgart': 'Bundesliga',
  'Gladbach': 'Bundesliga',
  'Freiburg': 'Bundesliga',
  'Werder Bremen': 'Bundesliga',
  'Hoffenheim': 'Bundesliga',
  'Union Berlin': 'Bundesliga',
  'Augsburg': 'Bundesliga',
  'Mainz 05': 'Bundesliga',
  'Heidenheim': 'Bundesliga',
  'Holstein Kiel': 'Bundesliga',
  'St. Pauli': 'Bundesliga',
  'Bochum': 'Bundesliga',
  'Wolfsburg': 'Bundesliga',
  'Köln': 'Bundesliga',
  'Schalke 04': 'Bundesliga',

  // La Liga
  'Real Madrid': 'La Liga',
  'Barcelona': 'La Liga',
  'Atlético Madrid': 'La Liga',
  'Athletic Club': 'La Liga',
  'Real Sociedad': 'La Liga',
  'Betis': 'La Liga',
  'Sevilla': 'La Liga',
  'Villarreal': 'La Liga',
  'Valencia': 'La Liga',
  'Celta Vigo': 'La Liga',
  'Osasuna': 'La Liga',
  'Espanyol': 'La Liga',
  'Alavés': 'La Liga',
  'Girona': 'La Liga',
  'Getafe': 'La Liga',
  'Las Palmas': 'La Liga',
  'Leganés': 'La Liga',
  'Mallorca': 'La Liga',
  'Rayo Vallecano': 'La Liga',
  'Valladolid': 'La Liga',

  // Serie A
  'Inter': 'Serie A',
  'Juventus': 'Serie A',
  'Milan': 'Serie A',
  'Napoli': 'Serie A',
  'Atalanta': 'Serie A',
  'Roma': 'Serie A',
  'Lazio': 'Serie A',
  'Bologna': 'Serie A',
  'Fiorentina': 'Serie A',
  'Torino': 'Serie A',
  'Genoa': 'Serie A',
  'Udinese': 'Serie A',
  'Como': 'Serie A',
  'Parma': 'Serie A',
  'Cagliari': 'Serie A',
  'Empoli': 'Serie A',
  'Hellas Verona': 'Serie A',
  'Lecce': 'Serie A',
  'Monza': 'Serie A',
  'Venezia': 'Serie A',

  // Ligue 1
  'Paris S-G': 'Ligue 1',
  'Marseille': 'Ligue 1',
  'Monaco': 'Ligue 1',
  'Lille': 'Ligue 1',
  'Lyon': 'Ligue 1',
  'Lens': 'Ligue 1',
  'Nice': 'Ligue 1',
  'Rennes': 'Ligue 1',
  'Strasbourg': 'Ligue 1',
  'Toulouse': 'Ligue 1',
  'Brest': 'Ligue 1',
  'Angers': 'Ligue 1',
  'Auxerre': 'Ligue 1',
  'Le Havre': 'Ligue 1',
  'Montpellier': 'Ligue 1',
  'Nantes': 'Ligue 1',
  // Newly active / Promoted / Transferred
  'Sunderland': 'Premier League',
  'Queens Park Rangers': 'Premier League',
  'Oviedo': 'La Liga',
  'Real Oviedo': 'La Liga',
  'Athletic Bilbao': 'La Liga',
  'Pisa': 'Serie A',
  'Paris FC': 'Ligue 1',
  'Pau': 'Ligue 1',
  '1. FC Kaiserslautern': 'Bundesliga',
  '1. FC Nürnberg': 'Bundesliga',
};

/**
 * Default starter club when a league is selected
 */
export const LEAGUE_DEFAULT_TEAMS = {
  'Premier League': 'Manchester City',
  'Bundesliga': 'Leverkusen',
  'La Liga': 'Real Madrid',
  'Serie A': 'Napoli',
  'Ligue 1': 'Paris S-G',
};

/**
 * Aliases: alternative name forms that appear in the UI, preset data, or
 * prediction results. Maps alternative → canonical dataset name.
 */
export const TEAM_ALIASES = {
  'man city': 'Manchester City',
  'man utd': 'Manchester Utd',
  'manchester united': 'Manchester Utd',
  'newcastle': 'Newcastle Utd',
  'newcastle united': 'Newcastle Utd',
  'nottingham forest': "Nott'ham Forest",
  'nottm forest': "Nott'ham Forest",
  'wolves': 'Wolves',
  'wolverhampton': 'Wolves',
  'wolverhampton wanderers': 'Wolves',
  'tottenham hotspur': 'Tottenham',
  'spurs': 'Tottenham',
  'west ham united': 'West Ham',
  'west bromwich albion': 'West Brom',
  'sheffield united': 'Sheffield Utd',
  'brighton and hove albion': 'Brighton',
  'brighton & hove albion': 'Brighton',
  'afc bournemouth': 'Bournemouth',
  'crystal palace': 'Crystal Palace',

  // Bundesliga
  'bayer leverkusen': 'Leverkusen',
  'bayer 04 leverkusen': 'Leverkusen',
  'borussia dortmund': 'Dortmund',
  'borussia mönchengladbach': 'Gladbach',
  'borussia monchengladbach': 'Gladbach',
  'eintracht frankfurt': 'Eint Frankfurt',
  'fc augsburg': 'Augsburg',
  'fc cologne': 'Köln',
  '1. fc köln': 'Köln',
  'vfb stuttgart': 'Stuttgart',
  'vfl wolfsburg': 'Wolfsburg',
  'sc freiburg': 'Freiburg',
  'tsg hoffenheim': 'Hoffenheim',
  '1. fc union berlin': 'Union Berlin',
  'fc union berlin': 'Union Berlin',
  'fc st. pauli': 'St. Pauli',
  '1. fc heidenheim': 'Heidenheim',
  'vfl bochum': 'Bochum',

  // La Liga
  'atletico madrid': 'Atlético Madrid',
  'atletico de madrid': 'Atlético Madrid',
  'real betis': 'Betis',
  'real betis balompié': 'Betis',
  'deportivo la coruña': 'La Coruña',
  'cd leganés': 'Leganés',
  'cd leganes': 'Leganés',
  'ud las palmas': 'Las Palmas',
  'ca osasuna': 'Osasuna',
  'rcd espanyol': 'Espanyol',
  'rcd mallorca': 'Mallorca',
  'rc celta': 'Celta Vigo',
  'rc celta de vigo': 'Celta Vigo',
  'celta': 'Celta Vigo',
  'real valladolid': 'Valladolid',

  // Serie A
  'ac milan': 'Milan',
  'inter milan': 'Inter',
  'internazionale': 'Inter',
  'fc internazionale': 'Inter',
  'as roma': 'Roma',
  'ss lazio': 'Lazio',
  'ssc napoli': 'Napoli',
  'ac monza': 'Monza',
  'us lecce': 'Lecce',
  'us salernitana': 'Salernitana',
  'uc sampdoria': 'Sampdoria',
  'hellas verona fc': 'Hellas Verona',
  'us cremonese': 'Cremonese',

  // Ligue 1
  'paris saint-germain': 'Paris S-G',
  'psg': 'Paris S-G',
  'paris sg': 'Paris S-G',
  'olympique de marseille': 'Marseille',
  'olympique lyonnais': 'Lyon',
  'olympique lyon': 'Lyon',
  'as monaco': 'Monaco',
  'losc lille': 'Lille',
  'stade rennais': 'Rennes',
  'rc lens': 'Lens',
  'ogc nice': 'Nice',
  'rc strasbourg': 'Strasbourg',
  'fc nantes': 'Nantes',
  'stade brestois': 'Brest',
  'as saint-étienne': 'Saint-Étienne',
  'st-etienne': 'Saint-Étienne',
  'stade de reims': 'Reims',

  // 2026/2027 test transfers & cross-league destinations
  'athletic bilbao': 'Athletic Club',
  'leicester': 'Leicester City',
  'sporting cp': 'Sporting CP',
  'sporting lisbon': 'Sporting CP',
  'red bull salzburg': 'Red Bull Salzburg',
  'rb salzburg': 'Red Bull Salzburg',
  'slavia prague': 'Slavia Prague',
  'qpr': 'Queens Park Rangers',
  'paris fc': 'Paris FC',
  'real oviedo': 'Oviedo',
  'pisa': 'Pisa',
  'sunderland': 'Sunderland',
  'kaiserslautern': '1. FC Kaiserslautern',
  '1. fc kaiserslautern': '1. FC Kaiserslautern',
  '1. fc nürnberg': '1. FC Nürnberg',
  'nürnberg': '1. FC Nürnberg',
  'anderlecht': 'Anderlecht',
  'celtic': 'Celtic',
  'rangers': 'Rangers',
  'braga': 'Braga',
  'westerlo': 'Westerlo',
  'zira': 'Zira',
  'estrela da amadora': 'Estrela da Amadora',
  'cruzeiro': 'Cruzeiro',
};

/**
 * Resolve a team name (from dataset, UI, or prediction result) to an ESPN CDN logo URL.
 * Uses exact match, canonical aliases, and fuzzy match.
 *
 * @param {string} teamName - The team name to resolve
 * @returns {{ url: string|null, urlLight: string|null, displayName: string }} - Logo URLs and canonical name
 */
export function getTeamCrest(teamName) {
  if (!teamName) return { url: null, urlLight: null, displayName: teamName };

  const trimmed = teamName.trim();

  // 1. Direct match
  if (TEAM_ESPN_IDS[trimmed]) {
    return {
      url: `${ESPN_CDN_BASE}/${TEAM_ESPN_IDS[trimmed]}.png`,
      urlLight: `${ESPN_CDN_LIGHT}/${TEAM_ESPN_IDS[trimmed]}.png`,
      displayName: trimmed,
    };
  }

  // 2. Alias match (case-insensitive)
  const lower = trimmed.toLowerCase();
  if (TEAM_ALIASES[lower]) {
    const canonical = TEAM_ALIASES[lower];
    const id = TEAM_ESPN_IDS[canonical];
    if (id) {
      return {
        url: `${ESPN_CDN_BASE}/${id}.png`,
        urlLight: `${ESPN_CDN_LIGHT}/${id}.png`,
        displayName: canonical,
      };
    }
  }

  // 3. Exact case-insensitive match against keys
  const keys = Object.keys(TEAM_ESPN_IDS);
  const exactCaseInsensitive = keys.find((k) => k.toLowerCase() === lower);
  if (exactCaseInsensitive) {
    return {
      url: `${ESPN_CDN_BASE}/${TEAM_ESPN_IDS[exactCaseInsensitive]}.png`,
      urlLight: `${ESPN_CDN_LIGHT}/${TEAM_ESPN_IDS[exactCaseInsensitive]}.png`,
      displayName: exactCaseInsensitive,
    };
  }

  // 4. Fuzzy substring match against canonical keys
  const fuzzyMatch = keys.find(
    (k) => k.toLowerCase().includes(lower) || lower.includes(k.toLowerCase())
  );
  if (fuzzyMatch) {
    return {
      url: `${ESPN_CDN_BASE}/${TEAM_ESPN_IDS[fuzzyMatch]}.png`,
      urlLight: `${ESPN_CDN_LIGHT}/${TEAM_ESPN_IDS[fuzzyMatch]}.png`,
      displayName: fuzzyMatch,
    };
  }

  // 5. Fuzzy match against aliases
  const aliasKeys = Object.keys(TEAM_ALIASES);
  const aliasMatch = aliasKeys.find(
    (k) => k.includes(lower) || lower.includes(k)
  );
  if (aliasMatch) {
    const canonical = TEAM_ALIASES[aliasMatch];
    const id = TEAM_ESPN_IDS[canonical];
    if (id) {
      return {
        url: `${ESPN_CDN_BASE}/${id}.png`,
        urlLight: `${ESPN_CDN_LIGHT}/${id}.png`,
        displayName: canonical,
      };
    }
  }

  // Fallback
  return { url: null, urlLight: null, displayName: trimmed };
}

/**
 * Get the canonical league for a given team
 * @param {string} teamName
 * @returns {string|null}
 */
export function getTeamLeague(teamName) {
  if (!teamName) return null;
  const crest = getTeamCrest(teamName);
  const canonical = crest?.displayName || teamName;
  return TEAM_LEAGUE_MAP[canonical] || null;
}

export default TEAM_ESPN_IDS;
