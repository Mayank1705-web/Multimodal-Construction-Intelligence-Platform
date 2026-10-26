# Known limitations

- Demo mode is rule based. It reads keywords, not images. Use a real provider for any image analysis.
- Image findings depend on photo quality, angle and lighting. A photo cannot measure crack width precisely, so widths are estimates.
- Safety and crack reports support, and do not replace, a competent person on site or a licensed structural engineer.
- Valuation uses model knowledge, not live listings or registry data. The demo provider uses a coarse city table. The result is indicative and not a certified valuation.
- Planning rates are India-oriented defaults converted with fixed approximate exchange rates (INR, USD, EUR, GBP, AED). Confirm quantities and rates with a quantity surveyor.
- The floor plan is a schematic room allocation, not a code-compliant architectural drawing.
- Weather uses Open-Meteo, needs internet access and covers five days.
- Standards named by the knowledge module must be checked against the current edition.
- There are no user accounts or access control. The history database is shared by everyone who can reach the API.
- Uploaded images are resized and sent to the model provider but are not stored on disk. Only filenames are kept in history.
