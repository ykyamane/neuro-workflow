import React, { useState, useCallback, createContext, useContext } from 'react';
import { Box } from '@chakra-ui/react';
import { Routes, Route } from 'react-router-dom';
import TabBar from './TabBar';
import HomeView from '../../views/home/homeView';
import FileView from '../../views/file/fileListView';
import FileListView from '../../views/file/fileListView';
import CreateFlowPj from '../../views/file/createView';
import BoxUpload from '../../views/box/uploadView';
import NotFoundView from '../../views/notFound/notFound';

export interface Tab {
  id: string;
  type: 'workflow' | 'jupyter';
  title: string;
  projectId?: string;
  url?: string;
  isActive: boolean;
}

interface TabContextType {
  tabs: Tab[];
  activeTabId: string;
  addJupyterTab: (projectId: string, projectName: string, url: string) => void;
  closeTab: (tabId: string) => void;
  switchTab: (tabId: string) => void;
}

const TabContext = createContext<TabContextType | undefined>(undefined);

export const useTabContext = () => {
  const context = useContext(TabContext);
  if (!context) {
    throw new Error('useTabContext must be used within TabManager');
  }
  return context;
};

export const TabManager: React.FC = () => {
  const [tabs, setTabs] = useState<Tab[]>([
    {
      id: 'workflow',
      type: 'workflow',
      title: 'Workflow',
      isActive: true,
    }
  ]);
  const [activeTabId, setActiveTabId] = useState('workflow');

  const addJupyterTab = useCallback((projectId: string, projectName: string, url: string) => {
    const existingTab = tabs.find(tab => tab.type === 'jupyter' && tab.id === `${projectId}-${projectName}`);
    
    if (existingTab) {
      // Activate an existing tab
      switchTab(existingTab.id);
      return;
    }

    const newTabId = `${projectId}-${projectName}`;
    const newTab: Tab = {
      id: newTabId,
      type: 'jupyter',
      //title: `${projectName} - JupyterLab`,
      title: `${projectName}`,
      projectId,
      url,
      isActive: true,
    };

    setTabs(prevTabs => {
      const updatedTabs = prevTabs.map(tab => ({ ...tab, isActive: false }));
      return [...updatedTabs, newTab];
    });
    setActiveTabId(newTabId);
  }, [tabs]);

  const closeTab = useCallback((tabId: string) => {
    if (tabId === 'workflow') return; // Workflow tab cannot be closed
    
    setTabs(prevTabs => {
      const updatedTabs = prevTabs.filter(tab => tab.id !== tabId);
      
      // Activate the workflow tab if a closed tab was active
      if (tabId === activeTabId) {
        setActiveTabId('workflow');
        return updatedTabs.map(tab => 
          tab.id === 'workflow' ? { ...tab, isActive: true } : { ...tab, isActive: false }
        );
      }
      
      return updatedTabs;
    });
  }, [activeTabId]);

  const switchTab = useCallback((tabId: string) => {
    setTabs(prevTabs => 
      prevTabs.map(tab => ({ ...tab, isActive: tab.id === tabId }))
    );
    setActiveTabId(tabId);
  }, []);

  const activeTab = tabs.find(tab => tab.id === activeTabId);

  const contextValue: TabContextType = {
    tabs,
    activeTabId,
    addJupyterTab,
    closeTab,
    switchTab,
  };

  return (
    <TabContext.Provider value={contextValue}>
      <Box 
        height="100%" 
        display="flex" 
        flexDirection="column"
        //marginLeft="320px"
      >
        {/* tab bar */}
        <TabBar />
        
        {/* Content area */}
        <Box flex="1" overflow="auto">
          {activeTab?.type === 'workflow' ? (
            // Normal routing for the Workflow tab
            <Routes>
              <Route path="/" element={<HomeView />} />
              <Route path="/file" element={<FileView />} />
              <Route path="/file/open" element={<FileListView />} />
              <Route path="/file/new" element={<CreateFlowPj />} />
              <Route path="/box/upload" element={<BoxUpload />} />
              <Route path="/*" element={<NotFoundView />} />
            </Routes>
          ) : activeTab?.type === 'jupyter' ? (
            // In the JupyterLab tab, it displays an iframe.
            <Box height="100%" w="100%">
              <iframe
                src={activeTab.url}
                width="100%"
                height="100%"
                style={{
                  border: 'none',
                  backgroundColor: 'white'
                }}
                title={activeTab.title}
                sandbox="allow-same-origin allow-scripts allow-forms allow-downloads allow-modals allow-popups allow-popups-to-escape-sandbox"
              />
            </Box>
          ) : null}
        </Box>
      </Box>
    </TabContext.Provider>
  );
};

export default TabManager;