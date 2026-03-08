# Localization (English + Thai)

## Feature Specification
Add language switching between English and Thai for all user-facing UI strings.

## Scope
- **In scope**: All frontend UI strings (~99), language switcher, speech recognition lang, localStorage persistence
- **Out of scope**: Backend API responses, AI chat responses (model handles this via prompt), game data from DB (titles, descriptions), PDF rulebook content

## User Stories
- As a Thai-speaking user, I want to switch the UI to Thai so I can navigate the app comfortably
- As a user, I want my language preference saved so it persists across sessions

## Acceptance Criteria
- [ ] Language switcher visible in the header
- [ ] All hardcoded UI strings translated to Thai
- [ ] Language preference persisted in localStorage
- [ ] Speech recognition lang updates with locale (en-US / th-TH)
- [ ] No layout breakage with Thai text (generally longer)
- [ ] All existing tests pass; new tests for i18n

## Technical Design
- **Library**: i18next + react-i18next (industry standard, lightweight)
- **Translation files**: `src/i18n/locales/en.json`, `src/i18n/locales/th.json`
- **Init**: `src/i18n/index.ts` — configures i18next with localStorage backend
- **Hook**: `useTranslation()` in every component with strings
- **Switcher**: `LanguageSwitcher` component in the header bar

## Todo
- [x] Install i18next + react-i18next
- [x] Create i18n config and translation files
- [x] Create LanguageSwitcher component
- [x] Replace strings in all components
- [x] Update SpeechRecognition lang
- [x] Add tests
- [x] Verify all existing tests pass
