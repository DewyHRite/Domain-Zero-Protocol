# WCAG 2.2 Complete Guide
<!-- Domain Zero Protocol v9.12.1 - Offline Reference -->

**Agent**: Nobara (Creative Strategy & UX)
**Last Updated**: 2025-12-26
**Source**: [W3C WCAG 2.2](https://www.w3.org/TR/WCAG22/)

---

## Table of Contents

1. [Overview](#overview)
2. [Conformance Levels](#conformance-levels)
3. [Perceivable](#1-perceivable)
4. [Operable](#2-operable)
5. [Understandable](#3-understandable)
6. [Robust](#4-robust)
7. [Testing Tools](#testing-tools)
8. [Quick Reference](#quick-reference)

---

## Overview

WCAG (Web Content Accessibility Guidelines) 2.2 provides guidelines for making web content accessible to people with disabilities, including:
- Visual impairments (blindness, low vision, color blindness)
- Hearing impairments (deafness, hard of hearing)
- Motor impairments (limited fine motor control)
- Cognitive impairments (learning disabilities, attention disorders)

### The Four Principles (POUR)

1. **Perceivable**: Information must be presentable in ways users can perceive
2. **Operable**: Interface components must be operable by all users
3. **Understandable**: Information and UI operation must be understandable
4. **Robust**: Content must work with current and future assistive technologies

---

## Conformance Levels

| Level | Description | Target Audience |
|-------|-------------|-----------------|
| **A** | Minimum accessibility | Basic compliance |
| **AA** | Mid-range accessibility | Most organizations (legal requirement in many jurisdictions) |
| **AAA** | Highest accessibility | Specialized accessibility needs |

**Recommendation**: Target Level AA for most projects.

---

## 1. Perceivable

### 1.1 Text Alternatives

**1.1.1 Non-text Content (Level A)**

All non-text content must have text alternatives.

```html
<!-- Images -->
<img src="chart.png" alt="Sales increased 25% in Q4 2024">

<!-- Decorative images -->
<img src="divider.png" alt="" role="presentation">

<!-- Complex images -->
<figure>
  <img src="flowchart.png" alt="User registration process">
  <figcaption>
    Detailed description: Users enter email, verify, set password, complete profile.
  </figcaption>
</figure>

<!-- Icons with meaning -->
<button>
  <svg aria-hidden="true">...</svg>
  <span class="sr-only">Close dialog</span>
</button>
```

### 1.2 Time-based Media

**1.2.1 Audio-only/Video-only (Level A)**
- Provide transcripts for audio-only content
- Provide audio descriptions or transcripts for video-only content

**1.2.2 Captions (Level A)**
- Provide synchronized captions for prerecorded video with audio

**1.2.3 Audio Description (Level A)**
- Provide audio descriptions for prerecorded video

```html
<video controls>
  <source src="video.mp4" type="video/mp4">
  <track kind="captions" src="captions.vtt" srclang="en" label="English">
  <track kind="descriptions" src="descriptions.vtt" srclang="en" label="Audio Descriptions">
</video>
```

### 1.3 Adaptable

**1.3.1 Info and Relationships (Level A)**

Use semantic HTML to convey structure:

```html
<!-- Headings hierarchy -->
<h1>Page Title</h1>
<h2>Section</h2>
<h3>Subsection</h3>

<!-- Lists -->
<ul>
  <li>Item 1</li>
  <li>Item 2</li>
</ul>

<!-- Tables with headers -->
<table>
  <caption>Quarterly Sales</caption>
  <thead>
    <tr>
      <th scope="col">Quarter</th>
      <th scope="col">Sales</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th scope="row">Q1</th>
      <td>$10,000</td>
    </tr>
  </tbody>
</table>

<!-- Form labels -->
<label for="email">Email Address</label>
<input type="email" id="email" name="email">
```

**1.3.2 Meaningful Sequence (Level A)**

Reading order must make sense when CSS is disabled.

**1.3.3 Sensory Characteristics (Level A)**

Don't rely solely on shape, color, size, or location:

```html
<!-- Bad -->
<p>Click the green button to continue</p>

<!-- Good -->
<p>Click the "Continue" button to proceed</p>
<button class="btn-primary">Continue</button>
```

### 1.4 Distinguishable

**1.4.1 Use of Color (Level A)**

Don't use color as the only visual means of conveying information:

```html
<!-- Bad: Color only indicates error -->
<input class="error-red">

<!-- Good: Color + icon + text -->
<input class="error" aria-describedby="email-error">
<span id="email-error" class="error-message">
  <svg aria-hidden="true"><!-- error icon --></svg>
  Email is required
</span>
```

**1.4.3 Contrast (Minimum) (Level AA)**

| Element | Minimum Contrast Ratio |
|---------|----------------------|
| Normal text | 4.5:1 |
| Large text (18pt+ or 14pt+ bold) | 3:1 |
| UI components and graphics | 3:1 |

```css
/* Good contrast examples */
.text-primary { color: #1a1a1a; } /* On white: 16.1:1 */
.text-link { color: #0066cc; }    /* On white: 5.9:1 */

/* Check with tools like WebAIM Contrast Checker */
```

**1.4.4 Resize Text (Level AA)**

Text must be resizable up to 200% without loss of functionality.

```css
/* Use relative units */
body { font-size: 16px; }
h1 { font-size: 2rem; }    /* Scales with user settings */
p { font-size: 1rem; }

/* Avoid fixed heights that clip text */
.container {
  min-height: 100px;  /* Good */
  /* height: 100px;   Bad - clips on zoom */
}
```

**1.4.10 Reflow (Level AA)**

Content must reflow without horizontal scrolling at 320px width (400% zoom).

```css
/* Responsive design */
.container {
  max-width: 100%;
  padding: 1rem;
}

/* Avoid fixed widths */
.card {
  width: 100%;
  max-width: 400px;
}
```

**1.4.11 Non-text Contrast (Level AA)**

UI components and graphics need 3:1 contrast ratio.

```css
/* Form inputs */
input {
  border: 2px solid #767676; /* 4.5:1 on white */
}

input:focus {
  outline: 3px solid #0066cc;
  outline-offset: 2px;
}
```

**1.4.12 Text Spacing (Level AA)**

Content must work with user-adjusted text spacing:
- Line height: 1.5x font size
- Paragraph spacing: 2x font size
- Letter spacing: 0.12x font size
- Word spacing: 0.16x font size

**1.4.13 Content on Hover or Focus (Level AA)**

Hover/focus content must be dismissible, hoverable, and persistent.

```css
.tooltip {
  /* Allow pointer to move to tooltip */
  pointer-events: auto;
}

/* Keep visible while hovering tooltip */
.trigger:hover + .tooltip,
.tooltip:hover {
  display: block;
}
```

---

## 2. Operable

### 2.1 Keyboard Accessible

**2.1.1 Keyboard (Level A)**

All functionality must be available via keyboard.

```html
<!-- Use native interactive elements -->
<button onclick="doAction()">Action</button>

<!-- If using div, add keyboard support -->
<div role="button" tabindex="0"
     onclick="doAction()"
     onkeydown="if(event.key==='Enter'||event.key===' ')doAction()">
  Action
</div>
```

**2.1.2 No Keyboard Trap (Level A)**

Users must be able to move focus away from any component.

```javascript
// Modal trap - allow Escape to close
modal.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') closeModal();
});
```

**2.1.4 Character Key Shortcuts (Level A)**

If using single character shortcuts, provide a way to turn them off or remap them.

### 2.2 Enough Time

**2.2.1 Timing Adjustable (Level A)**

For time limits, users must be able to:
- Turn off the time limit
- Adjust the time limit (at least 10x)
- Extend the time limit (with 20+ second warning)

```javascript
// Session timeout warning
function showTimeoutWarning() {
  const dialog = document.getElementById('timeout-dialog');
  dialog.showModal();
  // Provide option to extend
}
```

**2.2.2 Pause, Stop, Hide (Level A)**

Moving, blinking, or auto-updating content must be controllable.

```html
<div class="carousel" aria-live="polite">
  <button aria-label="Pause slideshow">Pause</button>
  <!-- slides -->
</div>
```

### 2.3 Seizures and Physical Reactions

**2.3.1 Three Flashes or Below Threshold (Level A)**

No content flashes more than 3 times per second.

### 2.4 Navigable

**2.4.1 Bypass Blocks (Level A)**

Provide skip links to bypass repeated content:

```html
<a href="#main-content" class="skip-link">Skip to main content</a>

<nav><!-- navigation --></nav>

<main id="main-content">
  <!-- Main content -->
</main>
```

```css
.skip-link {
  position: absolute;
  left: -9999px;
}

.skip-link:focus {
  left: 10px;
  top: 10px;
  z-index: 9999;
}
```

**2.4.2 Page Titled (Level A)**

```html
<title>Contact Us - Company Name</title>
```

**2.4.3 Focus Order (Level A)**

Focus order must be logical and meaningful.

```css
/* Don't use positive tabindex */
/* Bad: */ tabindex="1"
/* Good: */ tabindex="0" or no tabindex
```

**2.4.4 Link Purpose (In Context) (Level A)**

```html
<!-- Bad -->
<a href="report.pdf">Click here</a>

<!-- Good -->
<a href="report.pdf">Download Q4 2024 Sales Report (PDF, 2MB)</a>
```

**2.4.6 Headings and Labels (Level AA)**

Headings and labels must be descriptive.

**2.4.7 Focus Visible (Level AA)**

Focus indicator must be visible:

```css
:focus {
  outline: 3px solid #0066cc;
  outline-offset: 2px;
}

/* Don't remove focus styles */
/* Bad: */ :focus { outline: none; }
```

**2.4.11 Focus Not Obscured (Minimum) (Level AA)** - New in 2.2

Focused element must not be entirely hidden by other content.

### 2.5 Input Modalities

**2.5.1 Pointer Gestures (Level A)**

Complex gestures must have single-pointer alternatives.

**2.5.2 Pointer Cancellation (Level A)**

For single-pointer actions:
- Use `click`/`keyup` events (not `mousedown`/`keydown`)
- Allow users to abort actions

**2.5.3 Label in Name (Level A)**

Accessible name must contain visible label text:

```html
<!-- Good: accessible name matches visible text -->
<button>Submit Form</button>

<!-- Bad: mismatch -->
<button aria-label="Send">Submit</button>
```

**2.5.7 Dragging Movements (Level AA)** - New in 2.2

Provide non-dragging alternatives for drag operations.

**2.5.8 Target Size (Minimum) (Level AA)** - New in 2.2

Interactive targets must be at least 24x24 CSS pixels.

```css
button, a, input[type="checkbox"] {
  min-width: 44px;
  min-height: 44px;
}
```

---

## 3. Understandable

### 3.1 Readable

**3.1.1 Language of Page (Level A)**

```html
<html lang="en">
```

**3.1.2 Language of Parts (Level AA)**

```html
<p>The French word <span lang="fr">bonjour</span> means hello.</p>
```

### 3.2 Predictable

**3.2.1 On Focus (Level A)**

Focus alone must not cause unexpected changes.

**3.2.2 On Input (Level A)**

Input alone must not cause unexpected changes without warning.

```html
<!-- Bad: auto-submits on selection -->
<select onchange="this.form.submit()">

<!-- Good: requires explicit action -->
<select id="country">
<button type="submit">Apply</button>
```

**3.2.3 Consistent Navigation (Level AA)**

Navigation must be consistent across pages.

**3.2.4 Consistent Identification (Level AA)**

Components with the same function must be identified consistently.

### 3.3 Input Assistance

**3.3.1 Error Identification (Level A)**

Errors must be identified and described in text:

```html
<label for="email">Email</label>
<input type="email" id="email" aria-describedby="email-error" aria-invalid="true">
<span id="email-error" class="error">Please enter a valid email address</span>
```

**3.3.2 Labels or Instructions (Level A)**

Provide labels and instructions for user input.

**3.3.3 Error Suggestion (Level AA)**

Provide suggestions to fix errors when known:

```html
<span id="password-error">
  Password must contain at least 8 characters, one uppercase letter, and one number.
</span>
```

**3.3.4 Error Prevention (Legal, Financial, Data) (Level AA)**

For legal/financial/data submissions:
- Reversible: Allow undo
- Checked: Validate before submission
- Confirmed: Provide review step

**3.3.7 Redundant Entry (Level A)** - New in 2.2

Don't require users to re-enter information already provided.

**3.3.8 Accessible Authentication (Minimum) (Level AA)** - New in 2.2

Don't require cognitive function tests (puzzles, memory) for authentication. Allow:
- Password managers
- Copy/paste
- Alternative methods

---

## 4. Robust

### 4.1 Compatible

**4.1.2 Name, Role, Value (Level A)**

Custom components must expose name, role, and state:

```html
<!-- Custom checkbox -->
<div role="checkbox"
     aria-checked="false"
     aria-labelledby="label1"
     tabindex="0">
</div>
<span id="label1">Subscribe to newsletter</span>

<!-- Custom accordion -->
<button aria-expanded="false" aria-controls="panel1">
  Section 1
</button>
<div id="panel1" hidden>
  Content...
</div>
```

**4.1.3 Status Messages (Level AA)**

Status messages must be announced to assistive technologies:

```html
<!-- Live region for status updates -->
<div role="status" aria-live="polite">
  Form submitted successfully!
</div>

<!-- Alert for important messages -->
<div role="alert">
  Error: Connection lost. Reconnecting...
</div>
```

---

## Testing Tools

### Automated Testing

| Tool | Type | URL |
|------|------|-----|
| **axe DevTools** | Browser extension | [deque.com/axe](https://www.deque.com/axe/) |
| **WAVE** | Browser extension | [wave.webaim.org](https://wave.webaim.org/) |
| **Lighthouse** | Chrome DevTools | Built into Chrome |
| **pa11y** | CLI tool | [pa11y.org](https://pa11y.org/) |

### Manual Testing

1. **Keyboard Navigation**
   - Tab through entire page
   - Verify all interactive elements are reachable
   - Check focus visibility
   - Test Enter/Space activation

2. **Screen Reader Testing**
   - NVDA (Windows, free)
   - VoiceOver (macOS/iOS, built-in)
   - JAWS (Windows, commercial)

3. **Zoom Testing**
   - Test at 200% zoom
   - Test at 400% zoom
   - Verify no horizontal scrolling at 320px width

4. **Color Testing**
   - Check contrast ratios
   - Test without color (grayscale)
   - Test with color blindness simulators

---

## Quick Reference

### ARIA Landmarks

```html
<header role="banner">
<nav role="navigation">
<main role="main">
<aside role="complementary">
<footer role="contentinfo">
<form role="search">
```

### Common ARIA Attributes

```html
aria-label="Description"           <!-- Accessible name -->
aria-labelledby="id1 id2"          <!-- Reference to labels -->
aria-describedby="id"              <!-- Reference to description -->
aria-hidden="true"                 <!-- Hide from AT -->
aria-expanded="true|false"         <!-- Expandable state -->
aria-selected="true|false"         <!-- Selection state -->
aria-checked="true|false|mixed"    <!-- Checkbox state -->
aria-disabled="true"               <!-- Disabled state -->
aria-live="polite|assertive"       <!-- Live region -->
aria-invalid="true"                <!-- Invalid input -->
aria-required="true"               <!-- Required field -->
```

### Focus Management

```javascript
// Move focus to element
element.focus();

// Trap focus in modal
function trapFocus(modal) {
  const focusable = modal.querySelectorAll(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  );
  const first = focusable[0];
  const last = focusable[focusable.length - 1];

  modal.addEventListener('keydown', (e) => {
    if (e.key === 'Tab') {
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    }
  });
}
```

---

**Online References**:
- [W3C WCAG 2.2](https://www.w3.org/TR/WCAG22/)
- [WebAIM WCAG Checklist](https://webaim.org/standards/wcag/checklist)
- [W3C WAI-ARIA Practices](https://www.w3.org/WAI/ARIA/apg/)
