# CoVakeel frontend

The active frontend uses the provided CoVakeel website and app HTML/CSS directly,
including the original dot-tunnel canvas, reveal animations, responsive sidebar,
forms, and light/dark tokens. It runs through Vite as a two-page application.

- `index.html`: public website and inline/modal login/signup design.
- `app/index.html`: authenticated app, chat, search, profile, and appearance.
- `src/covakeel/api.js`: shared real FastAPI/JWT requests; no Claude key is sent to the browser.
- `src/covakeel/auth.js`: real email/password signup and email or username login.
- `src/covakeel/app.js`: real conversations, unchanged AI response text, and actual retrieved sources.
- `public/brand`: supplied SVG logos and favicon/app icons.

Run `npm run dev -- --host 127.0.0.1 --port 8081 --strictPort` or use the
repository's `scripts/start_local.sh`. Build with `npm run build`.
Legacy `/login`, `/register`, `/chat/:id`, and `/profile` links continue to work.

Google/SMS sign-in, payments, the product film, and final policy/contact content
were not configured by the existing project. Their designs remain present with
honest unavailable states. Device-only saved answers/projects are scoped by user;
account/profile and chat data persist in MongoDB. Existing React source files are
retained, but the new pages are the active build inputs.

# Welcome to your Lovable project

## Project info

**URL**: https://lovable.dev/projects/2b0cb427-0f92-4a1f-9727-896832a53244

## How can I edit this code?

There are several ways of editing your application.

**Use Lovable**

Simply visit the [Lovable Project](https://lovable.dev/projects/2b0cb427-0f92-4a1f-9727-896832a53244) and start prompting.

Changes made via Lovable will be committed automatically to this repo.

**Use your preferred IDE**

If you want to work locally using your own IDE, you can clone this repo and push changes. Pushed changes will also be reflected in Lovable.

The only requirement is having Node.js & npm installed - [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating)

Follow these steps:

```sh
# Step 1: Clone the repository using the project's Git URL.
git clone <YOUR_GIT_URL>

# Step 2: Navigate to the project directory.
cd <YOUR_PROJECT_NAME>

# Step 3: Install the necessary dependencies.
npm i

# Step 4: Start the development server with auto-reloading and an instant preview.
npm run dev
```

**Edit a file directly in GitHub**

- Navigate to the desired file(s).
- Click the "Edit" button (pencil icon) at the top right of the file view.
- Make your changes and commit the changes.

**Use GitHub Codespaces**

- Navigate to the main page of your repository.
- Click on the "Code" button (green button) near the top right.
- Select the "Codespaces" tab.
- Click on "New codespace" to launch a new Codespace environment.
- Edit files directly within the Codespace and commit and push your changes once you're done.

## What technologies are used for this project?

This project is built with:

- Vite
- TypeScript
- React
- shadcn-ui
- Tailwind CSS

## How can I deploy this project?

Simply open [Lovable](https://lovable.dev/projects/2b0cb427-0f92-4a1f-9727-896832a53244) and click on Share -> Publish.

## Can I connect a custom domain to my Lovable project?

Yes, you can!

To connect a domain, navigate to Project > Settings > Domains and click Connect Domain.

Read more here: [Setting up a custom domain](https://docs.lovable.dev/tips-tricks/custom-domain#step-by-step-guide)
