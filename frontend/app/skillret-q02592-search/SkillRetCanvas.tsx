"use client";

import { useEffect, useRef } from "react";
import VisualDiagram, {
  type ViewState,
  type VisualCanvasConfig,
  type VisualDiagramHandle,
  type VisualLinkProps,
} from "@horsecoder/visual-core";
import StandardModelEntity from "@/components/StandardModelEntity/wrapper";
import styles from "./page.module.css";

export type CanvasGraph = {
  nodes: { id: string; name: string; color: string; column: number; row: number }[];
  edges: { from: string; to: string; label: string }[];
};

const canvasConfig: VisualCanvasConfig = {
  toolbarConfig: [],
  globalConfig: { gridSize: 25 },
  elementConfig: {
    components: {
      model: { component: StandardModelEntity, minSize: { width: 156, height: 55 } },
    },
  },
  linkConfig: {
    components: {
      relation: { hasArrow: true, showName: false },
    },
  },
};

function LabeledLink({ link }: VisualLinkProps) {
  const { points, name, fromElementId, color = "#465b50" } = link.state;
  const end = points[points.length - 1];
  const start = points[0];
  const beforeEnd = points[points.length - 2];
  if (!start || !end || !beforeEnd) return null;

  const angle = Math.atan2(end.y - beforeEnd.y, end.x - beforeEnd.x) * 180 / Math.PI;
  const incoming = fromElementId === "INPUT";
  const labelPoint = incoming ? end : start;
  const labelY = labelPoint.y + (incoming ? -11 : 19);

  return (
    <g pointerEvents="none">
      <polyline points={points.map((point) => point.x + "," + point.y).join(" ")}
        fill="none" stroke={color} strokeWidth={2.5} strokeLinejoin="round" />
      <polygon points="-8,-5 -8,5 0,0" transform={`translate(${end.x},${end.y}) rotate(${angle})`} fill={color} />
      <text x={labelPoint.x + 7} y={labelY}
        fill={color} stroke="white" strokeWidth={4} paintOrder="stroke" fontSize={13}>{name}</text>
    </g>
  );
}

const namedLinks: VisualCanvasConfig = {
  ...canvasConfig,
  linkConfig: { components: { relation: { component: LabeledLink, hasArrow: true, showName: true } } },
};

function buildView(width: number, graph: CanvasGraph): ViewState {
  const { nodes, edges } = graph;
  const wide = width >= 680;
  const size = canvasConfig.elementConfig.components.model.minSize;
  return {
    id: "skillret-q-02592-search",
    elements: nodes.map(({ id, name, color, column, row }, index) => {
      const x = wide ? 88 + column * (width - 288) : Math.max(26, (width - size.width) / 2);
      const step = Math.min(83, 332 / (nodes.length - 1));
      const y = wide ? 30 + row * 143 : 38 + index * step;
      return {
        id,
        name,
        color,
        type: "model",
        x,
        y,
        select: false,
        locked: false,
        pendant: {
          data: {
            type: "model",
            detail: {
              id,
              model: { id, name: id, modelTitle: name, fields: [] },
              component: { id, modelId: id, isCollapse: false, x, y },
              fields: [],
              thirdParty: false,
              size: { ...size },
            },
          },
          onDataChange: () => {},
        },
      };
    }),
    links: edges.map(({ from, to, label }) => ({
      id: from + "-to-" + to,
      name: label,
      type: "relation",
      color: "#465b50",
      points: [],
      fromElementId: from,
      toElementId: to,
    })),
  };
}

export default function SkillRetCanvas({ graph }: { graph: CanvasGraph }) {
  const container = useRef<HTMLDivElement>(null);
  const diagram = useRef<VisualDiagramHandle>(null);

  useEffect(() => {
    const instance = diagram.current;
    if (instance && container.current) {
      const view = buildView(container.current.clientWidth, graph);
      instance.refreshCanvasLocked(view.id, false);
      instance.setView(view);
    }
  }, [graph]);

  return (
    <section className={styles.workflow} aria-label="技能编排画布">
      <p>箭头标出检索输入与候选去向。拖动节点可以调整布局。</p>
      <div ref={container} className={styles.flowCanvas}>
        <VisualDiagram ref={diagram} canvasConfig={namedLinks} />
      </div>
    </section>
  );
}

