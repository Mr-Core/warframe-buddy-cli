# Warframe Drop Data Parser & Search Engine

A Python-based tool for parsing, validating, and searching Warframe drop tables from the official Warframe website. This project transforms raw HTML drop tables into a structured, searchable database with optimized indexing.

## Features

### **Data Pipeline**
- **Web Scraping**: Fetches latest drop tables from Warframe's official site
- **Multi-Parser Architecture**: Separate parsers for Missions, Relics, and Sorties
- **Data Validation**: Comprehensive validation with error/warning reports
- **Automatic Filtering**: Removes inactive content (events, recalls)

### **Smart Search Engine**
- **Optimized Indexing**: Creates specialized indexes for lightning-fast searches
- **Case-Insensitive Search**: Find items with partial matching ("nikana" finds "Nikana Prime Blueprint")
- **Source-Specific Filtering**: 
  - Missions: Filter by planet, mission mode
  - Relics: Filter by tier, name, refinement
  - Sorties: Direct drop table access
- **Best Chance Sorting**: Results automatically sorted by highest drop chance

### **Dual Operation Modes**
- **Fresh Start Mode**: Fetch → Parse → Index → Save (complete pipeline)
- **Search-Only Mode**: Load pre-built indexes → Search (instant startup)
- **Development Mode**: Use cached data, skip web fetching for testing

## Project Architecture

```
warframe-buddy/
├── config.py              # Configuration (development/production mode)
├── main.py               # Main entry point with dual-mode interface
├── orchestrator.py       # Coordinates parsing and validation
├── search_engine.py      # Optimized indexing and search
├── base_parser.py        # Shared parsing utilities
├── mission_parser.py     # Mission drop table parser
├── relic_parser.py       # Relic drop table parser
├── sortie_parser.py      # Sortie drop table parser
├── fetch_data.py         # Web scraping module
├── .gitignore
└── README.md
```

## Data Flow

1. **Fetch**: Download latest HTML drop tables from Warframe
2. **Parse**: Extract structured data from HTML tables
3. **Validate**: Check data integrity and report issues
4. **Index**: Create optimized search indexes
5. **Search**: Query items with various filters
6. **Persist**: Save parsed data and indexes for fast loading

## Quick Start

### Installation
```bash
git clone https://github.com/YOUR_USERNAME/warframe-buddy.git
cd warframe-buddy
# Install dependencies if needed (requests, beautifulsoup4)
```

### Usage
```bash
# Run the program
python main.py

# Choose operation mode:
# 1. Fresh Start - Parse everything from scratch
# 2. Search Only - Use pre-built indexes
```

### Configuration
Edit `config.py`:
```python
DEVELOPMENT_MODE = True   # Use cached data, no web fetching
DEVELOPMENT_MODE = False  # Fetch fresh data from web
```

## Example Search
```
Search for: "forma"
Source type: relics
Filter by: tier="Lith"

Results:
1. Forma Blueprint - Lith A1 - 25.3% (Common)
2. Forma Blueprint - Lith B2 - 10.0% (Uncommon)
```

## Key Technologies
- **BeautifulSoup4**: HTML parsing and extraction
- **Optimized Indexing**: Custom hash-based indexes for O(1) lookups
- **Object-Oriented Design**: Clean separation of concerns with parser inheritance
- **Data Validation**: Comprehensive error checking and reporting

## Roadmap
- [ ] Scheduled daily data updates with intelligent caching
- [ ] Complete parser suite (enemies, bounties, syndicates, mods, etc.)
- [ ] Flask web interface
- [ ] REST API endpoints
- [ ] Docker containerization
- [ ] User favorites and history

**Development Approach:** Building incrementally from core data collection to full web interface, prioritizing data accuracy and search performance at every stage.

## Why This Project?
As a Warframe player, I wanted a fast, reliable way to find drop locations for specific items. The official drop tables are comprehensive but not easily searchable. This project solves that by creating a searchable database with the most up-to-date drop information.

---

**Note**: This is a fan project and is not affiliated with Digital Extremes or Warframe. All game data belongs to Digital Extremes.

---

*Built with Python • BeautifulSoup • Love for Warframe*
