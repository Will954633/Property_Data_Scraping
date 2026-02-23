"""
Generic Property Data Extraction Test
Last Updated: 04/02/2026, 7:50 am (Brisbane Time)

This script tests GENERIC extraction of ALL photos and text from ANY property website.
NO site-specific selectors or customization required.

Test Objective:
- Extract ALL images (including irrelevant ones like icons, UI buttons)
- Extract ALL text content (including irrelevant navigation, footer text)
- Work on ANY property website without modification
- Filtering of irrelevant content can be done later

Test Case:
- Target URL: https://raywhitemalanandco.com.au/properties/sold-residential/qld/varsity-lakes-4227/townhouse/3344866
"""

import asyncio
import json
from datetime import datetime
from playwright.async_api import async_playwright
from urllib.parse import urljoin, urlparse
import os

class GenericPropertyExtractor:
    def __init__(self, target_url):
        self.target_url = target_url
        self.results = {
            'test_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'target_url': target_url,
            'extraction_method': 'GENERIC - No site-specific selectors',
            'data': {}
        }
    
    async def extract_all_images(self, page):
        """
        Extract ALL images from the page using multiple methods.
        This is completely generic - works on any website.
        """
        print("\n=== Extracting ALL Images ===")
        
        all_images = []
        image_sources = set()  # To avoid duplicates
        
        try:
            # Method 1: Extract from <img> tags
            img_elements = await page.locator('img').all()
            print(f"Found {len(img_elements)} <img> elements")
            
            for img in img_elements:
                try:
                    # Get all possible image attributes
                    src = await img.get_attribute('src')
                    srcset = await img.get_attribute('srcset')
                    data_src = await img.get_attribute('data-src')
                    data_lazy = await img.get_attribute('data-lazy')
                    alt = await img.get_attribute('alt')
                    title = await img.get_attribute('title')
                    
                    # Get computed dimensions
                    box = await img.bounding_box()
                    width = box['width'] if box else None
                    height = box['height'] if box else None
                    
                    # Collect all possible sources
                    sources = [src, data_src, data_lazy]
                    
                    # Parse srcset if available
                    if srcset:
                        srcset_urls = [s.strip().split()[0] for s in srcset.split(',')]
                        sources.extend(srcset_urls)
                    
                    # Process each source
                    for source in sources:
                        if source and source not in image_sources:
                            # Convert relative URLs to absolute
                            absolute_url = urljoin(self.target_url, source)
                            
                            # Skip data URIs (base64 encoded images)
                            if not absolute_url.startswith('data:'):
                                image_sources.add(source)
                                all_images.append({
                                    'url': absolute_url,
                                    'original_src': source,
                                    'alt': alt or '',
                                    'title': title or '',
                                    'width': width,
                                    'height': height,
                                    'source_type': 'img_tag'
                                })
                except Exception as e:
                    print(f"  Warning: Could not extract image: {e}")
                    continue
            
            # Method 2: Extract from CSS background images
            background_images = await page.evaluate("""
                () => {
                    const elements = document.querySelectorAll('*');
                    const bgImages = [];
                    
                    elements.forEach(el => {
                        const style = window.getComputedStyle(el);
                        const bgImage = style.backgroundImage;
                        
                        if (bgImage && bgImage !== 'none') {
                            // Extract URL from url("...") or url('...')
                            const matches = bgImage.match(/url\\(['"]?([^'"\\)]+)['"]?\\)/g);
                            if (matches) {
                                matches.forEach(match => {
                                    const url = match.replace(/url\\(['"]?/, '').replace(/['"]?\\)/, '');
                                    bgImages.push(url);
                                });
                            }
                        }
                    });
                    
                    return [...new Set(bgImages)];
                }
            """)
            
            print(f"Found {len(background_images)} CSS background images")
            
            for bg_url in background_images:
                if bg_url not in image_sources:
                    absolute_url = urljoin(self.target_url, bg_url)
                    if not absolute_url.startswith('data:'):
                        image_sources.add(bg_url)
                        all_images.append({
                            'url': absolute_url,
                            'original_src': bg_url,
                            'alt': '',
                            'title': '',
                            'width': None,
                            'height': None,
                            'source_type': 'css_background'
                        })
            
            # Method 3: Extract from <picture> and <source> elements
            picture_sources = await page.locator('picture source, source').all()
            print(f"Found {len(picture_sources)} <picture>/<source> elements")
            
            for source in picture_sources:
                try:
                    srcset = await source.get_attribute('srcset')
                    src = await source.get_attribute('src')
                    
                    sources = [src]
                    if srcset:
                        srcset_urls = [s.strip().split()[0] for s in srcset.split(',')]
                        sources.extend(srcset_urls)
                    
                    for source_url in sources:
                        if source_url and source_url not in image_sources:
                            absolute_url = urljoin(self.target_url, source_url)
                            if not absolute_url.startswith('data:'):
                                image_sources.add(source_url)
                                all_images.append({
                                    'url': absolute_url,
                                    'original_src': source_url,
                                    'alt': '',
                                    'title': '',
                                    'width': None,
                                    'height': None,
                                    'source_type': 'picture_source'
                                })
                except:
                    continue
            
            # Method 4: Extract from JavaScript variables (common in SPAs)
            js_images = await page.evaluate("""
                () => {
                    const images = [];
                    const text = document.documentElement.innerHTML;
                    
                    // Look for common image URL patterns in the HTML/JS
                    const patterns = [
                        /https?:\\/\\/[^\\s"'<>]+\\.(?:jpg|jpeg|png|gif|webp|svg)/gi,
                        /"(https?:\\/\\/[^"]+\\.(?:jpg|jpeg|png|gif|webp|svg))"/gi,
                        /'(https?:\\/\\/[^']+\\.(?:jpg|jpeg|png|gif|webp|svg))'/gi
                    ];
                    
                    patterns.forEach(pattern => {
                        const matches = text.match(pattern);
                        if (matches) {
                            images.push(...matches);
                        }
                    });
                    
                    return [...new Set(images)];
                }
            """)
            
            print(f"Found {len(js_images)} images in JavaScript/HTML")
            
            for js_url in js_images:
                # Clean up the URL - remove quotes
                js_url = js_url.strip('"\'')
                if js_url not in image_sources:
                    if not js_url.startswith('data:'):
                        image_sources.add(js_url)
                        all_images.append({
                            'url': js_url,
                            'original_src': js_url,
                            'alt': '',
                            'title': '',
                            'width': None,
                            'height': None,
                            'source_type': 'javascript'
                        })
            
            print(f"\n✓ Total unique images extracted: {len(all_images)}")
            return all_images
            
        except Exception as e:
            print(f"✗ Error extracting images: {e}")
            return []
    
    async def extract_all_text(self, page):
        """
        Extract ALL text content from the page.
        Multiple methods to ensure we get everything.
        """
        print("\n=== Extracting ALL Text Content ===")
        
        text_data = {}
        
        try:
            # Method 1: Get all visible text
            body_text = await page.locator('body').inner_text()
            text_data['visible_text'] = body_text
            text_data['visible_text_length'] = len(body_text)
            print(f"✓ Extracted {len(body_text)} characters of visible text")
            
            # Method 2: Get page title
            text_data['page_title'] = await page.title()
            print(f"✓ Page title: {text_data['page_title']}")
            
            # Method 3: Get meta descriptions and keywords
            meta_description = await page.locator('meta[name="description"]').get_attribute('content')
            meta_keywords = await page.locator('meta[name="keywords"]').get_attribute('content')
            text_data['meta_description'] = meta_description or ''
            text_data['meta_keywords'] = meta_keywords or ''
            
            # Method 4: Extract all headings (h1-h6)
            headings = {}
            for i in range(1, 7):
                heading_elements = await page.locator(f'h{i}').all()
                heading_texts = []
                for h in heading_elements:
                    try:
                        text = await h.inner_text()
                        if text.strip():
                            heading_texts.append(text.strip())
                    except:
                        continue
                headings[f'h{i}'] = heading_texts
            
            text_data['headings'] = headings
            total_headings = sum(len(v) for v in headings.values())
            print(f"✓ Extracted {total_headings} headings")
            
            # Method 5: Extract all paragraph text
            paragraphs = await page.locator('p').all()
            paragraph_texts = []
            for p in paragraphs:
                try:
                    text = await p.inner_text()
                    if text.strip():
                        paragraph_texts.append(text.strip())
                except:
                    continue
            text_data['paragraphs'] = paragraph_texts
            print(f"✓ Extracted {len(paragraph_texts)} paragraphs")
            
            # Method 6: Extract all list items
            list_items = await page.locator('li').all()
            list_texts = []
            for li in list_items:
                try:
                    text = await li.inner_text()
                    if text.strip():
                        list_texts.append(text.strip())
                except:
                    continue
            text_data['list_items'] = list_texts
            print(f"✓ Extracted {len(list_texts)} list items")
            
            # Method 7: Extract all table data
            tables = await page.locator('table').all()
            table_data = []
            for table in tables:
                try:
                    text = await table.inner_text()
                    if text.strip():
                        table_data.append(text.strip())
                except:
                    continue
            text_data['tables'] = table_data
            print(f"✓ Extracted {len(table_data)} tables")
            
            # Method 8: Extract all link text
            links = await page.locator('a').all()
            link_data = []
            for link in links:
                try:
                    text = await link.inner_text()
                    href = await link.get_attribute('href')
                    if text.strip() or href:
                        link_data.append({
                            'text': text.strip(),
                            'href': urljoin(self.target_url, href) if href else ''
                        })
                except:
                    continue
            text_data['links'] = link_data
            print(f"✓ Extracted {len(link_data)} links")
            
            # Method 9: Extract structured data (JSON-LD, microdata)
            structured_data = await page.evaluate("""
                () => {
                    const scripts = document.querySelectorAll('script[type="application/ld+json"]');
                    const data = [];
                    scripts.forEach(script => {
                        try {
                            data.push(JSON.parse(script.textContent));
                        } catch (e) {}
                    });
                    return data;
                }
            """)
            text_data['structured_data'] = structured_data
            print(f"✓ Extracted {len(structured_data)} structured data blocks")
            
            # Method 10: Get all text from specific semantic elements
            semantic_elements = ['article', 'section', 'aside', 'nav', 'header', 'footer', 'main']
            semantic_text = {}
            for element in semantic_elements:
                elements = await page.locator(element).all()
                texts = []
                for el in elements:
                    try:
                        text = await el.inner_text()
                        if text.strip():
                            texts.append(text.strip())
                    except:
                        continue
                semantic_text[element] = texts
            text_data['semantic_elements'] = semantic_text
            
            return text_data
            
        except Exception as e:
            print(f"✗ Error extracting text: {e}")
            return {}
    
    async def extract_page_metadata(self, page):
        """Extract general page metadata"""
        print("\n=== Extracting Page Metadata ===")
        
        metadata = {}
        
        try:
            metadata['url'] = page.url
            metadata['title'] = await page.title()
            
            # Get all meta tags
            meta_tags = await page.evaluate("""
                () => {
                    const metas = document.querySelectorAll('meta');
                    const data = {};
                    metas.forEach(meta => {
                        const name = meta.getAttribute('name') || meta.getAttribute('property');
                        const content = meta.getAttribute('content');
                        if (name && content) {
                            data[name] = content;
                        }
                    });
                    return data;
                }
            """)
            metadata['meta_tags'] = meta_tags
            
            # Get canonical URL
            canonical = await page.locator('link[rel="canonical"]').get_attribute('href')
            metadata['canonical_url'] = canonical or ''
            
            print(f"✓ Extracted metadata for: {metadata['title']}")
            return metadata
            
        except Exception as e:
            print(f"✗ Error extracting metadata: {e}")
            return {}
    
    async def run_extraction(self, headless=True, save_screenshots=True):
        """Run the complete generic extraction"""
        print("=" * 70)
        print("GENERIC PROPERTY DATA EXTRACTION TEST")
        print("=" * 70)
        print(f"Target URL: {self.target_url}")
        print(f"Method: GENERIC - No site-specific selectors")
        print("=" * 70)
        
        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch(headless=headless)
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            page = await context.new_page()
            
            try:
                # Navigate to the target URL
                print(f"\nNavigating to: {self.target_url}")
                await page.goto(self.target_url, wait_until='networkidle', timeout=30000)
                print("✓ Page loaded successfully")
                
                # Wait for dynamic content
                await asyncio.sleep(3)
                
                # Take initial screenshot
                if save_screenshots:
                    screenshot_path = '12_Individual_Property_Web_Search/screenshots/initial_page.png'
                    os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
                    await page.screenshot(path=screenshot_path, full_page=True)
                    print(f"✓ Screenshot saved: {screenshot_path}")
                
                # Extract metadata
                self.results['data']['metadata'] = await self.extract_page_metadata(page)
                
                # Extract all images
                self.results['data']['images'] = await self.extract_all_images(page)
                
                # Extract all text
                self.results['data']['text'] = await self.extract_all_text(page)
                
                # Calculate statistics
                self.results['statistics'] = {
                    'total_images': len(self.results['data']['images']),
                    'total_text_length': self.results['data']['text'].get('visible_text_length', 0),
                    'total_headings': sum(len(v) for v in self.results['data']['text'].get('headings', {}).values()),
                    'total_paragraphs': len(self.results['data']['text'].get('paragraphs', [])),
                    'total_links': len(self.results['data']['text'].get('links', [])),
                    'total_list_items': len(self.results['data']['text'].get('list_items', [])),
                    'extraction_success': True
                }
                
            except Exception as e:
                print(f"\n✗ Extraction failed: {e}")
                self.results['statistics'] = {
                    'extraction_success': False,
                    'error': str(e)
                }
            
            finally:
                await browser.close()
        
        return self.results
    
    def save_results(self, filename='generic_extraction_results.json'):
        """Save results to JSON file"""
        filepath = f'12_Individual_Property_Web_Search/{filename}'
        
        # Create a summary version (without full text to keep file size manageable)
        summary_results = {
            'test_date': self.results['test_date'],
            'target_url': self.results['target_url'],
            'extraction_method': self.results['extraction_method'],
            'statistics': self.results['statistics'],
            'metadata': self.results['data'].get('metadata', {}),
            'sample_images': self.results['data'].get('images', [])[:10],  # First 10 images
            'sample_text': {
                'page_title': self.results['data'].get('text', {}).get('page_title', ''),
                'headings': self.results['data'].get('text', {}).get('headings', {}),
                'first_5_paragraphs': self.results['data'].get('text', {}).get('paragraphs', [])[:5],
                'visible_text_preview': self.results['data'].get('text', {}).get('visible_text', '')[:500]
            }
        }
        
        with open(filepath, 'w') as f:
            json.dump(summary_results, f, indent=2)
        print(f"\n✓ Summary results saved to {filepath}")
        
        # Save full results
        full_filepath = f'12_Individual_Property_Web_Search/generic_extraction_full.json'
        with open(full_filepath, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"✓ Full results saved to {full_filepath}")
    
    def print_summary(self):
        """Print a summary of extraction results"""
        print("\n" + "=" * 70)
        print("EXTRACTION SUMMARY")
        print("=" * 70)
        
        stats = self.results.get('statistics', {})
        
        if stats.get('extraction_success'):
            print(f"\n✓ EXTRACTION SUCCESSFUL")
            print(f"\nImages Extracted: {stats.get('total_images', 0)}")
            print(f"Text Length: {stats.get('total_text_length', 0):,} characters")
            print(f"Headings: {stats.get('total_headings', 0)}")
            print(f"Paragraphs: {stats.get('total_paragraphs', 0)}")
            print(f"Links: {stats.get('total_links', 0)}")
            print(f"List Items: {stats.get('total_list_items', 0)}")
            
            # Show sample images
            images = self.results['data'].get('images', [])
            if images:
                print(f"\nSample Images (first 5):")
                for i, img in enumerate(images[:5], 1):
                    print(f"  {i}. {img['url'][:80]}...")
                    print(f"     Type: {img['source_type']}, Alt: {img['alt'][:50]}")
            
            # Show sample text
            text_data = self.results['data'].get('text', {})
            if text_data.get('page_title'):
                print(f"\nPage Title: {text_data['page_title']}")
            
            headings = text_data.get('headings', {})
            if headings.get('h1'):
                print(f"\nH1 Headings:")
                for h1 in headings['h1'][:3]:
                    print(f"  - {h1}")
            
        else:
            print(f"\n✗ EXTRACTION FAILED")
            print(f"Error: {stats.get('error', 'Unknown error')}")
        
        print("\n" + "=" * 70)


async def main():
    """Main function to run the test"""
    
    # Target URL - Ray White property page
    target_url = "https://raywhitemalanandco.com.au/properties/sold-residential/qld/varsity-lakes-4227/townhouse/3344866"
    
    # Create extractor
    extractor = GenericPropertyExtractor(target_url)
    
    # Run extraction (set headless=False to see the browser)
    print("\nStarting generic extraction...")
    results = await extractor.run_extraction(headless=True, save_screenshots=True)
    
    # Print summary
    extractor.print_summary()
    
    # Save results
    extractor.save_results()
    
    print("\n✓ Test complete!")
    print("\nNext Steps:")
    print("1. Review the results in generic_extraction_results.json")
    print("2. Check screenshots/ folder for page capture")
    print("3. If successful, this method can be used on ANY property website")
    print("4. Later, we can add filtering to remove irrelevant images/text")


if __name__ == '__main__':
    asyncio.run(main())
