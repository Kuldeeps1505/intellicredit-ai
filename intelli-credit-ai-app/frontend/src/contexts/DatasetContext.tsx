import React, { createContext, useContext, useState } from "react";
import { DatasetId, getDataset, Dataset } from "@/lib/demoData";

interface DatasetContextValue {
  activeDataset: DatasetId;
  setActiveDataset: (id: DatasetId) => void;
  dataset: Dataset;
}

const DatasetContext = createContext<DatasetContextValue | null>(null);

export const DatasetProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [activeDataset, setActiveDataset] = useState<DatasetId>("fraud");
  return (
    <DatasetContext.Provider value={{ activeDataset, setActiveDataset, dataset: getDataset(activeDataset) }}>
      {children}
    </DatasetContext.Provider>
  );
};

export const useDataset = () => {
  const ctx = useContext(DatasetContext);
  if (!ctx) throw new Error("useDataset must be used within DatasetProvider");
  return ctx;
};
