# Banks Savings Calculator - Webflow Version

This repository contains the Webflow-friendly version of the Banks Savings Calculator. The code has been converted from a Python-based application to pure HTML, CSS, and JavaScript for compatibility with Webflow.

## Structure
- `index.html`: Main HTML structure
- `css/styles.css`: Custom styles
- `js/calculator.js`: Calculator logic and interactions

## Webflow Implementation Instructions

1. **CSS Setup**:
   - In Webflow, go to the project settings
   - Navigate to the Custom Code section
   - Copy the contents of `css/styles.css` into the Head Code section

2. **JavaScript Setup**:
   - Host the `calculator.js` file on a CDN (e.g., GitHub Pages or your preferred hosting service)
   - Add the script tag to your Webflow project's Custom Code section:
     ```html
     <script src="your-cdn-url/calculator.js"></script>
     ```

3. **HTML Structure**:
   - Create the necessary elements in Webflow's designer:
     - Sidebar section with client inputs
     - Main content section with prediction cards
   - Make sure to use the same class names and IDs as specified in the HTML file
   - Add the Bootstrap CDN links in your project settings

4. **Required External Dependencies**:
   - Bootstrap 5.1.3 CSS and JS
   - Bootstrap Icons 1.7.2

## Calculator Features
- Separate calculations for Startup and SME clients
- Three engagement levels (Low, Medium, High)
- Dynamic updates based on user input
- Responsive design
- Tooltips for engagement levels

## Notes
- All calculations are performed client-side using JavaScript
- No server-side code is required
- The calculator will work entirely within Webflow's hosting environment
