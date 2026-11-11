# CampusAI · VSSUT campus navigation

CampusAI's navigation page is configured for Veer Surendra Sai University of Technology (VSSUT), Burla, Sambalpur, Odisha, India. Its Google Map opens at the official VSSUT website's embedded campus location. The VSSUT boundary is left off until verified boundary data is available.

## Run locally

1. Install the Python packages in `requirements.txt`.
2. Copy `.env.example` to `.env` and enter the key/password you need.
3. Launch Streamlit from the CampusAI folder:

   ```sh
   streamlit run app.py
   ```

CampusAI reads `.env` directly at runtime; you do not need to export the values first.

You can also set `GOOGLE_MAPS_BROWSER_API_KEY` and `CAMPUS_ADMIN_PASSWORD` in Streamlit's top-level secrets, for example in `.streamlit/secrets.toml`:

```toml
GOOGLE_MAPS_BROWSER_API_KEY = "your-browser-restricted-key"
CAMPUS_ADMIN_PASSWORD = "choose-a-strong-admin-password"
CAMPUS_LOGIN_ADMIN_EMAIL = "admin@campusai.com"
CAMPUS_LOGIN_ADMIN_PASSWORD = "choose-a-different-strong-admin-password"
```

The login administrator is created only when `CAMPUS_LOGIN_ADMIN_PASSWORD` is set. Student and faculty registration passwords are stored as salted PBKDF2 hashes. Older local plaintext-password rows are re-hashed after a successful login. The local SQLite database is not included in GitHub.

The key is read at runtime. The Maps JavaScript API requires a browser key, so visitors can see that key in their browser; restrict it in Google Cloud by website referrer and API. Do not put a real key in source control. `.env` and `.streamlit/secrets.toml` are ignored by Git.

## Google Cloud setup

1. Create a Google Cloud project and attach an enabled billing account. Maps Platform usage can incur charges; set quotas and budget alerts in Google Cloud.
2. Enable **Maps JavaScript API**, **Places API (New)**, and **Routes API** for the project.
3. Create an API key. Restrict its application to website referrers used by the app (for local development, `http://localhost:8501/*`; add the exact HTTPS domain used in deployment).
4. Restrict the key to the three enabled APIs above. Do not use an unrestricted production key. If a future feature geocodes verified postal addresses, enable **Geocoding API** separately and add it to the API restriction.
5. Set the key as `GOOGLE_MAPS_BROWSER_API_KEY` in the environment or Streamlit secrets. Set `CAMPUS_ADMIN_PASSWORD` to enable the campus data editor.

The app uses the Maps JavaScript API for the interactive Map/Satellite views, Places API (New) Text Search for campus place lookup, and the Maps JavaScript Routes Library for walking directions. Places search runs only when a student submits a search, requests a small field set and up to ten results, and route calls are reused for the same origin/destination pair during the active map session. Google Maps may reject requests when billing, API enablement, quotas, or key restrictions are missing; the app reports the error and offers an optional uploaded image fallback.

## VSSUT campus data

`data/campus_graph.json` is the campus location and pedestrian graph database. Its official VSSUT campus-area viewport comes from the university's Google Maps embed. The file includes requested campus locations, but leaves building coordinates unset until an administrator verifies them. It currently contains a **sample demonstration graph**: its distances and connections are illustrative and are not confirmed VSSUT paths. They are never presented as real-world directions.

With `CAMPUS_ADMIN_PASSWORD` configured, open **Administrator · verify campus locations and paths** on the Campus Map page. Click the location on Google Maps, then confirm and save its coordinates with a verifier name and source note. You can also confirm a Google Places result for that building. Use the connection editor to replace or remove sample paths and add verified pedestrian connections with measured distances. Algorithm paths are drawn on the map only when every edge in that result is verified and the route nodes have verified coordinates. Do not add guessed pins, junctions, road connections, or distances.

Google walking directions come from Google's Routes API. BFS, DFS, and A* run independently on the VSSUT graph in the Python backend. BFS minimizes edge count, DFS does not promise the shortest route, and A* uses a zero admissible heuristic while the graph is sample or partially verified; once all graph edges and node coordinates are verified, it can use straight-line distance as the heuristic. Algorithm results label the data source. They are not claims about Google's route.

When the Google API key is missing or unusable, the start/destination selectors still provide a no-key Google Maps walking-directions link. Google Maps opens separately and resolves the selected location names; students should confirm the endpoints because unverified campus pins can be ambiguous. The in-app interactive map, live Places search, and in-app route geometry require the API key. Students may expand the optional image fallback to upload a static VSSUT map reference; CampusAI does not silently substitute the existing project image or an unrelated map.
