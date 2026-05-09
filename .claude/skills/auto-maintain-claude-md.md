# Skill: Auto-maintain CLAUDE.md

When making significant changes to the project, automatically update CLAUDE.md to reflect:

1. **New dependencies**: When adding a new package (Python or npm), update the "Tech Stack" section.
2. **New commands**: When adding a new Makefile target, update the "Commands" section.
3. **New conventions**: When establishing a new pattern or convention, add it to the appropriate "Conventions" subsection.
4. **Architecture changes**: When modifying the project structure or adding new services, update the "Architecture" and "Project Structure" sections.
5. **Environment variables**: When adding new env vars, update both `.env.example` and the "Environment Variables" section in CLAUDE.md.

## Rules
- Keep CLAUDE.md concise and scannable
- Do not add implementation details -- only document conventions, commands, and architecture
- Always keep the "Commands" section in sync with actual Makefile targets
- Update version numbers when upgrading dependencies
