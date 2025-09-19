import React, {useEffect, useRef} from 'react';

type NodeMap = Record<string, { href: string; title?: string }>;

interface Props {
  /** CSS selector for the container that holds the Mermaid SVG (e.g., '#design-flowchart') */
  containerSelector: string;
  /** Map of Mermaid node ids to destination URLs and optional native tooltip text */
  nodeMap: NodeMap;
}

/**
 * Attaches native title tooltips and click navigation to Mermaid-rendered nodes.
 * Works post-render and avoids Mermaid's tooltip system to prevent runtime errors.
 */
const AttachMermaidLinks: React.FC<Props> = ({containerSelector, nodeMap}) => {
  const observerRef = useRef<MutationObserver | null>(null);
  const enhancedRef = useRef<Set<string>>(new Set());
  const pollTimerRef = useRef<number | null>(null);

  useEffect(() => {
    const container = document.querySelector(containerSelector) as HTMLElement | null;
    if (!container) return;

    // Helper to get a Mermaid node group robustly across versions
    const findNodeGroup = (root: HTMLElement, id: string): SVGGElement | null => {
      // Preferred: data-id
      let g: SVGGElement | null = root.querySelector(`g[data-id="${id}"]`);
      if (g) return g;
      // Sometimes id is set directly
      g = root.querySelector(`g#${CSS.escape(id)}`);
      if (g) return g;
      // Flowchart often prefixes ids (e.g., flowchart-Aleya, flowchart-Aleya-xxx)
      g = root.querySelector(`g[id*="${CSS.escape(id)}"]`);
      if (g && (g as SVGGElement)) return g as SVGGElement;
      return null;
    };

    const enhanceNode = (id: string, href: string, title?: string) => {
      if (enhancedRef.current.has(id)) return; // already enhanced
      const g = findNodeGroup(container, id);
      if (!g) return;

      // Mark to avoid duplicate listeners
      enhancedRef.current.add(id);
      g.setAttribute('data-linked', 'true');

      // Tooltip via native <title>
      if (title) {
        let titleEl: Element | null = g.querySelector('title');
        // Ensure it's an SVG <title>; otherwise create one
        const isSvgTitle = titleEl?.namespaceURI === 'http://www.w3.org/2000/svg';
        if (!titleEl || !isSvgTitle) {
          titleEl = document.createElementNS('http://www.w3.org/2000/svg', 'title');
          g.prepend(titleEl);
        }
        titleEl.textContent = title;
      }

      // Click + keyboard accessibility
      (g as unknown as HTMLElement).style.cursor = 'pointer';
      g.setAttribute('role', 'link');
      g.setAttribute('tabindex', '0');

      const navigate = () => {
        // Use reliable navigation (full assign) to avoid router integration issues
        window.location.assign(href);
      };

      const onClick = (e: Event) => {
        if ((e.target as HTMLElement)?.closest('a')) return;
        navigate();
      };
      const onKey = (e: KeyboardEvent) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          navigate();
        }
      };

      g.addEventListener('click', onClick);
      g.addEventListener('keydown', onKey as unknown as EventListener);

      // Store handlers for cleanup
      (g as any).__attachHandlers = {onClick, onKey};
    };

    const tryEnhanceAll = () => {
      Object.entries(nodeMap).forEach(([id, {href, title}]) => enhanceNode(id, href, title));
    };

    // 1) Initial attempt
    tryEnhanceAll();

    // 2) Observe DOM mutations (Mermaid renders asynchronously)
    observerRef.current = new MutationObserver(() => {
      tryEnhanceAll();
    });
    observerRef.current.observe(container, {childList: true, subtree: true});

    // 3) Short polling fallback (in case initial render is delayed)
    const start = Date.now();
    pollTimerRef.current = window.setInterval(() => {
      tryEnhanceAll();
      if (Date.now() - start > 3000) {
        if (pollTimerRef.current) window.clearInterval(pollTimerRef.current);
        pollTimerRef.current = null;
      }
    }, 200);

    return () => {
      if (observerRef.current) {
        observerRef.current.disconnect();
        observerRef.current = null;
      }
      if (pollTimerRef.current) {
        window.clearInterval(pollTimerRef.current);
        pollTimerRef.current = null;
      }
      // Clean up listeners
      Object.keys(nodeMap).forEach((id) => {
        const g = findNodeGroup(container, id);
        if (g && (g as any).__attachHandlers) {
          const {onClick, onKey} = (g as any).__attachHandlers;
          g.removeEventListener('click', onClick);
          g.removeEventListener('keydown', onKey);
          delete (g as any).__attachHandlers;
        }
      });
      enhancedRef.current.clear();
    };
  }, [containerSelector, nodeMap]);

  return null;
};

export default AttachMermaidLinks;
