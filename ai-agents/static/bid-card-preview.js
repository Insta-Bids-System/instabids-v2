/**
 * Bid Card Link Preview JavaScript
 * Automatically converts bid card URLs into visual preview cards
 */

class BidCardPreviewer {
    constructor() {
        this.previewCache = new Map();
        this.init();
    }

    init() {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.scanForBidCardLinks());
        } else {
            this.scanForBidCardLinks();
        }

        // Also scan when new content is added dynamically
        this.observeContentChanges();
    }

    scanForBidCardLinks() {
        // Find all text nodes that contain bid card URLs
        const bidCardUrlPattern = /https?:\/\/[^\s]*\/api\/bid-cards\/[a-f0-9-]+\/preview/gi;
        
        // Get all text nodes in the document
        const walker = document.createTreeWalker(
            document.body,
            NodeFilter.SHOW_TEXT,
            null,
            false
        );

        const textNodes = [];
        let node;
        while (node = walker.nextNode()) {
            if (bidCardUrlPattern.test(node.textContent)) {
                textNodes.push(node);
            }
        }

        // Process each text node that contains bid card URLs
        textNodes.forEach(textNode => {
            this.processTextNode(textNode);
        });
    }

    processTextNode(textNode) {
        const bidCardUrlPattern = /https?:\/\/[^\s]*\/api\/bid-cards\/[a-f0-9-]+\/preview/gi;
        const text = textNode.textContent;
        const matches = [...text.matchAll(bidCardUrlPattern)];

        if (matches.length === 0) return;

        // Create a container to hold the text and preview cards
        const container = document.createElement('div');
        container.className = 'bid-card-text-container';

        let lastIndex = 0;
        matches.forEach(match => {
            const url = match[0];
            const startIndex = match.index;

            // Add text before the URL
            if (startIndex > lastIndex) {
                const textBefore = text.substring(lastIndex, startIndex);
                container.appendChild(document.createTextNode(textBefore));
            }

            // Add the URL as a link
            const link = document.createElement('a');
            link.href = url;
            link.textContent = url;
            link.target = '_blank';
            link.style.color = '#1a73e8';
            container.appendChild(link);

            // Add line break
            container.appendChild(document.createElement('br'));

            // Add the preview card
            const previewCard = this.createPreviewCard(url);
            container.appendChild(previewCard);

            lastIndex = startIndex + url.length;
        });

        // Add remaining text
        if (lastIndex < text.length) {
            const textAfter = text.substring(lastIndex);
            container.appendChild(document.createTextNode(textAfter));
        }

        // Replace the original text node with our container
        textNode.parentNode.replaceChild(container, textNode);
    }

    createPreviewCard(url) {
        const card = document.createElement('div');
        card.className = 'bid-card-preview-card';
        card.style.cssText = `
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            overflow: hidden;
            margin: 10px 0;
            background: white;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            max-width: 500px;
            cursor: pointer;
            transition: box-shadow 0.2s ease;
        `;

        card.addEventListener('mouseenter', () => {
            card.style.boxShadow = '0 4px 16px rgba(0,0,0,0.15)';
        });

        card.addEventListener('mouseleave', () => {
            card.style.boxShadow = '0 2px 8px rgba(0,0,0,0.1)';
        });

        card.addEventListener('click', () => {
            window.open(url, '_blank');
        });

        // Load preview data
        this.loadPreviewData(url, card);

        return card;
    }

    async loadPreviewData(url, card) {
        try {
            // Show loading state
            card.innerHTML = `
                <div style="padding: 20px; text-align: center; color: #666;">
                    <div style="margin-bottom: 10px;">🔄</div>
                    Loading bid card preview...
                </div>
            `;

            // Extract bid card ID from URL
            const bidCardId = url.match(/\/bid-cards\/([a-f0-9-]+)\/preview/)?.[1];
            if (!bidCardId) throw new Error('Invalid bid card URL');

            // Fetch preview data from API
            const apiUrl = url.replace('/preview', '');
            const response = await fetch(apiUrl);
            
            if (!response.ok) throw new Error('Failed to load bid card data');
            
            const data = await response.json();

            // Render the preview card
            card.innerHTML = `
                <div style="
                    width: 100%;
                    height: 120px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    font-size: 32px;
                ">
                    🔨
                </div>
                <div style="padding: 16px;">
                    <div style="
                        font-size: 18px;
                        font-weight: bold;
                        color: #1a73e8;
                        margin-bottom: 8px;
                    ">
                        ${data.project_type.replace('_', ' ').toUpperCase()} - ${data.budget_display}
                    </div>
                    <div style="
                        color: #666;
                        font-size: 14px;
                        line-height: 1.4;
                        margin-bottom: 8px;
                    ">
                        ${data.project_type.replace('_', ' ')} project in ${data.location.city || 'your area'}. 
                        Timeline: ${data.timeline}. Click to view details and submit your bid.
                    </div>
                    <div style="color: #999; font-size: 12px;">
                        instabids.com
                    </div>
                </div>
            `;

        } catch (error) {
            console.error('Error loading bid card preview:', error);
            card.innerHTML = `
                <div style="padding: 16px;">
                    <div style="
                        font-size: 16px;
                        font-weight: bold;
                        color: #1a73e8;
                        margin-bottom: 8px;
                    ">
                        Instabids Project Preview
                    </div>
                    <div style="
                        color: #666;
                        font-size: 14px;
                        line-height: 1.4;
                        margin-bottom: 8px;
                    ">
                        Click to view project details and submit your bid.
                    </div>
                    <div style="color: #999; font-size: 12px;">
                        instabids.com
                    </div>
                </div>
            `;
        }
    }

    observeContentChanges() {
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.type === 'childList') {
                    mutation.addedNodes.forEach((node) => {
                        if (node.nodeType === Node.TEXT_NODE) {
                            const bidCardUrlPattern = /https?:\/\/[^\s]*\/api\/bid-cards\/[a-f0-9-]+\/preview/gi;
                            if (bidCardUrlPattern.test(node.textContent)) {
                                this.processTextNode(node);
                            }
                        } else if (node.nodeType === Node.ELEMENT_NODE) {
                            // Scan new element for bid card links
                            const textNodes = [];
                            const walker = document.createTreeWalker(
                                node,
                                NodeFilter.SHOW_TEXT,
                                null,
                                false
                            );
                            let textNode;
                            while (textNode = walker.nextNode()) {
                                const bidCardUrlPattern = /https?:\/\/[^\s]*\/api\/bid-cards\/[a-f0-9-]+\/preview/gi;
                                if (bidCardUrlPattern.test(textNode.textContent)) {
                                    textNodes.push(textNode);
                                }
                            }
                            textNodes.forEach(tn => this.processTextNode(tn));
                        }
                    });
                }
            });
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }
}

// Auto-initialize when script loads
if (typeof window !== 'undefined') {
    new BidCardPreviewer();
}