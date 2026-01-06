/**
 * Playwright HTML Editor Service
 * Fast HTML editing using browser automation
 */

const express = require('express');
const { chromium } = require('playwright');
const redis = require('redis');

const app = express();
const PORT = process.env.PORT || 3001;
const REDIS_URL = process.env.REDIS_URL || 'redis://redis:6379/0';

app.use(express.json({ limit: '50mb' }));

// Redis client (optional, for caching)
let redisClient = null;

async function initRedis() {
    try {
        redisClient = redis.createClient({ url: REDIS_URL });
        await redisClient.connect();
        console.log('Redis connected successfully');
    } catch (error) {
        console.warn('Redis connection failed, continuing without cache:', error.message);
        redisClient = null;
    }
}

// Health check
app.get('/health', (req, res) => {
    res.json({
        status: 'healthy',
        service: 'playwright-editor',
        version: '1.0.0'
    });
});

// Simple text edit endpoint
app.post('/edit-simple', async (req, res) => {
    try {
        const { html, instruction } = req.body;

        if (!html || !instruction) {
            return res.status(400).json({
                error: 'Missing required fields: html, instruction'
            });
        }

        console.log(`Editing HTML with instruction: ${instruction.substring(0, 100)}`);

        // Launch browser
        const browser = await chromium.launch({
            headless: true,
            args: ['--no-sandbox', '--disable-setuid-sandbox']
        });

        const context = await browser.newContext();
        const page = await context.newPage();

        // Load HTML
        await page.setContent(html);

        // Parse instruction and apply edit
        const editedHtml = await applySimpleEdit(page, instruction);

        await browser.close();

        console.log('Edit completed successfully');

        res.json({
            success: true,
            html: editedHtml
        });

    } catch (error) {
        console.error('Error editing HTML:', error);
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Get DOM structure
app.post('/get-dom', async (req, res) => {
    try {
        const { html } = req.body;

        if (!html) {
            return res.status(400).json({
                error: 'Missing required field: html'
            });
        }

        const browser = await chromium.launch({
            headless: true,
            args: ['--no-sandbox', '--disable-setuid-sandbox']
        });

        const context = await browser.newContext();
        const page = await context.newPage();
        await page.setContent(html);

        // Extract DOM structure
        const domStructure = await page.evaluate(() => {
            function getElementInfo(element) {
                return {
                    tag: element.tagName.toLowerCase(),
                    id: element.id || null,
                    classes: Array.from(element.classList),
                    text: element.textContent?.substring(0, 100),
                    children: Array.from(element.children).map(getElementInfo)
                };
            }
            return getElementInfo(document.body);
        });

        await browser.close();

        res.json({
            success: true,
            dom: domStructure
        });

    } catch (error) {
        console.error('Error getting DOM:', error);
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

/**
 * Apply simple edit based on instruction
 */
async function applySimpleEdit(page, instruction) {
    const instructionLower = instruction.toLowerCase();

    // Text change patterns
    if (instructionLower.includes('change') && instructionLower.includes('text')) {
        return await changeText(page, instruction);
    }

    // Color change patterns
    if (instructionLower.includes('change') && (instructionLower.includes('color') || instructionLower.includes('colour'))) {
        return await changeColor(page, instruction);
    }

    // Background change
    if (instructionLower.includes('change') && instructionLower.includes('background')) {
        return await changeBackground(page, instruction);
    }

    // Hide/show elements
    if (instructionLower.includes('hide') || instructionLower.includes('remove')) {
        return await hideElement(page, instruction);
    }

    // Default: return original HTML
    return await page.content();
}

/**
 * Change text content
 */
async function changeText(page, instruction) {
    // Multiple patterns to extract selector and new text
    const patterns = [
        /change\s+(?:the\s+)?(.+?)\s+text\s+to\s+["']?(.+?)["']?$/i,
        /change\s+["']?(.+?)["']?\s+to\s+["']?(.+?)["']?$/i,
        /set\s+(?:the\s+)?(.+?)\s+(?:text\s+)?to\s+["']?(.+?)["']?$/i,
        /update\s+(?:the\s+)?(.+?)\s+(?:text\s+)?to\s+["']?(.+?)["']?$/i
    ];

    let selector = null;
    let newText = null;

    for (const pattern of patterns) {
        const match = instruction.match(pattern);
        if (match) {
            selector = match[1].trim().toLowerCase();
            newText = match[2].trim();
            break;
        }
    }

    if (selector && newText) {
        // Build list of selectors to try
        const selectors = [];

        // If it looks like a CSS selector (starts with . or #), use directly
        if (selector.startsWith('.') || selector.startsWith('#')) {
            selectors.push(selector);
        } else {
            // Try various interpretations
            selectors.push(
                selector,                           // Direct tag name
                `.${selector}`,                     // Class
                `#${selector}`,                     // ID
                `[class*="${selector}"]`            // Partial class match
            );

            // Special handling for common terms
            if (selector.includes('header') || selector.includes('title') || selector.includes('heading')) {
                selectors.unshift('h1', 'h2', '.title', '.heading', 'header h1');
            }
            if (selector.includes('button')) {
                selectors.unshift('button', '.btn', '[class*="button"]');
            }
        }

        for (const sel of selectors) {
            try {
                const changed = await page.evaluate(({ selector, text }) => {
                    const element = document.querySelector(selector);
                    if (element) {
                        element.textContent = text;
                        return true;
                    }
                    return false;
                }, { selector: sel, text: newText });

                if (changed) break;
            } catch (e) {
                // Try next selector
            }
        }
    }

    return await page.content();
}

/**
 * Change color
 */
async function changeColor(page, instruction) {
    const colorMatch = instruction.match(/(blue|red|green|yellow|black|white|gray|purple|pink|orange|#[0-9a-fA-F]{3,6})/i);

    if (colorMatch) {
        const color = colorMatch[1];

        // Try to extract CSS selector from instruction
        // Patterns: "change color of .class to blue", "change a.neo-brutal color to blue"
        const selectorPatterns = [
            /change\s+(?:the\s+)?color\s+of\s+([.#\w-]+(?:\.[.#\w-]+)*)\s+to/i,
            /change\s+([.#\w-]+(?:\.[.#\w-]+)*)\s+color\s+to/i,
            /make\s+([.#\w-]+(?:\.[.#\w-]+)*)\s+(?:color\s+)?(?:be\s+)?/i,
            /([.#][\w-]+(?:\.[\w-]+)*)\s+(?:to|should be|color)/i
        ];

        let selector = null;
        for (const pattern of selectorPatterns) {
            const match = instruction.match(pattern);
            if (match && match[1]) {
                selector = match[1];
                break;
            }
        }

        if (selector) {
            // Use extracted selector
            const changed = await page.evaluate(({ sel, c }) => {
                const elements = document.querySelectorAll(sel);
                if (elements.length > 0) {
                    elements.forEach(el => el.style.color = c);
                    return true;
                }
                return false;
            }, { sel: selector, c: color });

            if (changed) {
                return await page.content();
            }
        }

        // Fallback to keyword-based targeting
        if (instruction.includes('header')) {
            await page.evaluate((c) => {
                const header = document.querySelector('header, h1, .header');
                if (header) header.style.color = c;
            }, color);
        } else if (instruction.includes('background')) {
            await page.evaluate((c) => {
                document.body.style.backgroundColor = c;
            }, color);
        } else if (instruction.includes('button')) {
            await page.evaluate((c) => {
                document.querySelectorAll('button, .btn, [class*="button"]').forEach(el => el.style.color = c);
            }, color);
        } else if (instruction.includes('link')) {
            await page.evaluate((c) => {
                document.querySelectorAll('a').forEach(el => el.style.color = c);
            }, color);
        } else {
            // Default: change first heading
            await page.evaluate((c) => {
                const heading = document.querySelector('h1, h2');
                if (heading) heading.style.color = c;
            }, color);
        }
    }

    return await page.content();
}

/**
 * Change background
 */
async function changeBackground(page, instruction) {
    const colorMatch = instruction.match(/(blue|red|green|yellow|black|white|gray|purple|pink|orange|#[0-9a-fA-F]{6})/i);

    if (colorMatch) {
        const color = colorMatch[1];

        if (instruction.includes('header')) {
            await page.evaluate((c) => {
                const header = document.querySelector('header, .header');
                if (header) header.style.backgroundColor = c;
            }, color);
        } else {
            await page.evaluate((c) => {
                document.body.style.backgroundColor = c;
            }, color);
        }
    }

    return await page.content();
}

/**
 * Hide element
 */
async function hideElement(page, instruction) {
    // Extract element to hide
    const match = instruction.match(/hide|remove\s+(.+)/i);

    if (match) {
        const element = match[1].toLowerCase();

        await page.evaluate((el) => {
            const selectors = [el, `.${el}`, `#${el}`, `[data-section="${el}"]`];
            for (const sel of selectors) {
                try {
                    const elem = document.querySelector(sel);
                    if (elem) {
                        elem.style.display = 'none';
                        break;
                    }
                } catch (e) {
                    // Try next selector
                }
            }
        }, element);
    }

    return await page.content();
}

// Get detailed DOM with bounding boxes (for visual overlay)
app.post('/get-dom-detailed', async (req, res) => {
    try {
        const { html, include_bounds } = req.body;

        if (!html) {
            return res.status(400).json({
                error: 'Missing required field: html'
            });
        }

        const browser = await chromium.launch({
            headless: true,
            args: ['--no-sandbox', '--disable-setuid-sandbox']
        });

        const context = await browser.newContext({
            viewport: { width: 1280, height: 800 }
        });
        const page = await context.newPage();
        await page.setContent(html);

        // Wait for any animations/styles to settle
        await page.waitForTimeout(100);

        // Extract detailed DOM with bounds
        const domStructure = await page.evaluate((includeBounds) => {
            function getElementInfo(element, depth = 0) {
                if (depth > 15) return null; // Limit depth

                const rect = includeBounds ? element.getBoundingClientRect() : null;

                // Get direct text content (not from children)
                let directText = '';
                for (const child of element.childNodes) {
                    if (child.nodeType === Node.TEXT_NODE) {
                        directText += child.textContent.trim();
                    }
                }

                const children = Array.from(element.children)
                    .filter(child => {
                        const tag = child.tagName.toLowerCase();
                        return !['script', 'style', 'noscript', 'svg', 'path'].includes(tag);
                    })
                    .map(child => getElementInfo(child, depth + 1))
                    .filter(Boolean);

                return {
                    tag: element.tagName.toLowerCase(),
                    id: element.id || null,
                    classes: Array.from(element.classList),
                    text: directText.substring(0, 200) || null,
                    bounds: rect ? {
                        top: Math.round(rect.top),
                        left: Math.round(rect.left),
                        width: Math.round(rect.width),
                        height: Math.round(rect.height)
                    } : null,
                    depth: depth,
                    children: children
                };
            }
            return getElementInfo(document.body);
        }, include_bounds !== false);

        await browser.close();

        res.json({
            success: true,
            dom: domStructure
        });

    } catch (error) {
        console.error('Error getting detailed DOM:', error);
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Edit specific component by selector
app.post('/edit-component', async (req, res) => {
    try {
        const { html, selector, edit_type, edit_value } = req.body;

        if (!html || !selector || !edit_type) {
            return res.status(400).json({
                error: 'Missing required fields: html, selector, edit_type'
            });
        }

        console.log(`Editing component: ${selector} with ${edit_type}`);

        const browser = await chromium.launch({
            headless: true,
            args: ['--no-sandbox', '--disable-setuid-sandbox']
        });

        const context = await browser.newContext();
        const page = await context.newPage();
        await page.setContent(html);

        // Apply edit based on type
        const editResult = await page.evaluate(({ selector, editType, editValue }) => {
            const element = document.querySelector(selector);
            if (!element) {
                return { success: false, error: `Element not found: ${selector}` };
            }

            try {
                switch (editType) {
                    case 'text':
                        element.textContent = editValue;
                        break;

                    case 'innerHTML':
                        element.innerHTML = editValue;
                        break;

                    case 'style':
                        // editValue is an object like {color: 'red', fontSize: '16px'}
                        if (typeof editValue === 'object') {
                            Object.entries(editValue).forEach(([prop, val]) => {
                                element.style[prop] = val;
                            });
                        }
                        break;

                    case 'attribute':
                        // editValue is {name: 'href', value: 'https://...'}
                        if (editValue.name && editValue.value !== undefined) {
                            element.setAttribute(editValue.name, editValue.value);
                        }
                        break;

                    case 'class':
                        // editValue is {add: ['new-class'], remove: ['old-class']}
                        if (editValue.add && Array.isArray(editValue.add)) {
                            element.classList.add(...editValue.add);
                        }
                        if (editValue.remove && Array.isArray(editValue.remove)) {
                            element.classList.remove(...editValue.remove);
                        }
                        break;

                    case 'replace':
                        // Replace entire element HTML
                        element.outerHTML = editValue;
                        break;

                    case 'hide':
                        element.style.display = 'none';
                        break;

                    case 'show':
                        element.style.display = '';
                        break;

                    default:
                        return { success: false, error: `Unknown edit type: ${editType}` };
                }

                return { success: true };
            } catch (e) {
                return { success: false, error: e.message };
            }
        }, { selector, editType: edit_type, editValue: edit_value });

        if (!editResult.success) {
            await browser.close();
            return res.status(400).json({
                success: false,
                error: editResult.error
            });
        }

        const editedHtml = await page.content();
        await browser.close();

        console.log('Component edit completed successfully');

        res.json({
            success: true,
            html: editedHtml
        });

    } catch (error) {
        console.error('Error editing component:', error);
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Get element HTML by selector
app.post('/get-element', async (req, res) => {
    try {
        const { html, selector } = req.body;

        if (!html || !selector) {
            return res.status(400).json({
                error: 'Missing required fields: html, selector'
            });
        }

        const browser = await chromium.launch({
            headless: true,
            args: ['--no-sandbox', '--disable-setuid-sandbox']
        });

        const page = await browser.newPage();
        await page.setContent(html);

        const elementData = await page.evaluate((sel) => {
            const element = document.querySelector(sel);
            if (!element) {
                return null;
            }
            return {
                element_html: element.outerHTML,
                text_content: element.textContent,
                tag: element.tagName.toLowerCase(),
                id: element.id,
                classes: Array.from(element.classList)
            };
        }, selector);

        await browser.close();

        if (!elementData) {
            return res.status(404).json({
                success: false,
                error: 'Element not found'
            });
        }

        res.json({
            success: true,
            ...elementData
        });

    } catch (error) {
        console.error('Error getting element:', error);
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Start server
async function start() {
    await initRedis();

    app.listen(PORT, '0.0.0.0', () => {
        console.log(`Playwright HTML Editor running on port ${PORT}`);
    });
}

start();
