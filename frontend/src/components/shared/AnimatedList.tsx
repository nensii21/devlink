/**
 * AnimatedList / AnimatedListItem — staggered fade+slide for lists.
 *
 * AnimatedList is the container that controls stagger timing.
 * AnimatedListItem wraps each row/card within the list.
 *
 * Usage:
 *   <AnimatedList>
 *     {projects.map((p) => (
 *       <AnimatedListItem key={p.id}>
 *         <ProjectCard project={p} />
 *       </AnimatedListItem>
 *     ))}
 *   </AnimatedList>
 */

import { motion, useReducedMotion } from "framer-motion";
import type { ReactNode } from "react";
import { listContainerVariants, listItemVariants, listItemVariantsReduced } from "@/lib/motion";

interface AnimatedListProps {
  children: ReactNode;
  className?: string;
}

export function AnimatedList({ children, className }: AnimatedListProps) {
  return (
    <motion.div
      className={className}
      variants={listContainerVariants}
      initial="initial"
      animate="animate"
    >
      {children}
    </motion.div>
  );
}

interface AnimatedListItemProps {
  children: ReactNode;
  className?: string;
}

export function AnimatedListItem({ children, className }: AnimatedListItemProps) {
  const shouldReduce = useReducedMotion();
  const variants = shouldReduce ? listItemVariantsReduced : listItemVariants;

  return (
    <motion.div className={className} variants={variants}>
      {children}
    </motion.div>
  );
}
