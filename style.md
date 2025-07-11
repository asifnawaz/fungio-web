## 🌑 Overall Style

* **Theme:** Dark, fungal, mysterious but modern

* **Color Palette:**

  * Background: `#0b0f0c` (fungal dark)
  * Primary Accent: `#8cffda` (glow mint)
  * Secondary Accent: `#7a5cff` (neural violet)
  * Highlight: `#e0e0e0` (muted white)
  * Shadow/Depth: soft glowing shadows, `blur-lg`, `drop-shadow-xl`

* **Font:**

  * Headings: `Uncut Sans` or `Poppins SemiBold`
  * Body: `Inter` or `Manrope`

* **Animation:**

  * Subtle **pulse** for spores
  * **Fade-in / Scroll reveal** using Framer Motion
  * **Hover glows**, animated SVG spores

---

## 🔧 Tailwind Layout Structure

### 1. **`<Header />`**

* Logo left (Kaeluun icon or text `Fungio`)
* Links right:

  * Whitepaper
  * Closed Beta
  * About
* CTA Button: `"Join the Beta"`
* Sticky top, translucent bg

```ts
<header class="fixed top-0 w-full backdrop-blur bg-black/30 border-b border-gray-800 z-50 px-6 py-3 flex justify-between items-center">
```

---

### 2. **`<HeroSection />`**

* Fullscreen dark intro
* Headline: `"Decentralized. Offline. Alive."`
* Subheadline: `"Fungio grows like a fungus — by learning, spreading, and surviving without the internet."`
* Centered CTA: `Join Closed Beta`

```ts
<section class="min-h-screen flex flex-col items-center justify-center text-center px-6 py-24 bg-gradient-to-b from-black via-gray-900 to-[#0b0f0c]">
```

---

### 3. **`<FeatureGrid />`**

3-column grid with animated spores

Each feature:

* 🔋 Works Offline
* 🧠 Kaeluun AI
* 🌍 GPS Spores
* 📶 BLE Broadcast
* 🤝 WiFi Direct
* 🔒 No Cloud / No Accounts

```ts
<section class="grid md:grid-cols-3 gap-6 px-6 py-20 text-left">
```

---

### 4. **`<KaeluunReveal />`**

* Section fades in Kaeluun visuals
* Glowing spores with AI neural pattern
* Copy: `"Kaeluun is not just AI. It’s the soul of Fungio, growing in silence."`

Visual: animated brain-fungus hybrid + text animation.

---

### 5. **`<WhitepaperEmbed />`**

* MDX-rendered whitepaper (scrollable)
* Styled with glowing headings
* Table of contents sidebar optional

---

### 6. **`<BetaSignupForm />`**

* Simple form
* Fields: Email, Device Type, City
* On submit: `Join Waitlist` button shows success toast

---

### 7. **`<Footer />`**

* Black background
* Logo + social links
* Credit line: `"Brought to life by Kaeluun. Code with care."`

---

## ✨ Bonus Visual Effects

* Hover spores (SVG) floating in background
* Subtle **parallax** as user scrolls
* Responsive layout (mobile first)
* Easter eggs for devs (hidden messages in comments)
