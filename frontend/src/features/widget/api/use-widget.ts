import { useState } from "react";

export const useWidget = () => {
  const [widgetOpen, setWidgetOpen] = useState(false);
  const toggleWidget = () => {
    setWidgetOpen(!widgetOpen);
  };
  return { widgetOpen, toggleWidget, setWidgetOpen };
};
