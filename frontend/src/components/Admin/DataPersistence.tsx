import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { useAppDispatch, useAppSelector } from '../../hooks/redux';
import { api } from '../../services/api';

const DataPersistenceContainer = styled.div`
  padding: 20px;
  background: ${props => props.theme.colors.background};
  color: ${props => props.theme.colors.text};
  min-height: 100vh;
`;

const Section = styled.div`
  background: ${props => props.theme.colors.cardBackground};
  border: 1px solid ${props => props.theme.colors.border};
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
`;

const SectionTitle = styled.h2`
  color: ${props => props.theme.colors.primary};
  margin-bottom: 15px;
  font-size: 1.2em;
`;

const Button = styled.button<{ variant?: 'primary' | 'danger' | 'secondary' }>`
  background: ${props => {
    switch (props.variant) {
      case 'danger': return props.theme.colors.danger;
      case 'secondary': return props.theme.colors.secondary;
      default: return props.theme.colors.primary;
    }
  }};
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 4px;
  cursor: pointer;
  margin: 5px;
  font-size: 14px;
  
  &:hover {
    opacity: 0.9;
  }
  
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`;

const Input = styled.input`
  background: ${props => props.theme.colors.inputBackground};
  color: ${props => props.theme.colors.text};
  border: 1px solid ${props => props.theme.colors.border};
  border-radius: 4px;
  padding: 8px 12px;
  margin: 5px;
  font-size: 14px;
  width: 200px;
`;

const Checkbox = styled.input`
  margin: 5px 10px 5px 0;
`;

const Label = styled.label`
  display: flex;
  align-items: center;
  margin: 5px 0;
  font-size: 14px;
`;

const StatusMessage = styled.div<{ type: 'success' | 'error' | 'warning' }>`
  padding: 10px;
  border-radius: 4px;
  margin: 10px 0;
  background: ${props => {
    switch (props.type) {
      case 'success': return '#d4edda';
      case 'error': return '#f8d7da';
      case 'warning': return '#fff3cd';
      default: return '#e2e3e5';
    }
  }};
  color: ${props => {
    switch (props.type) {
      case 'success': return '#155724';
      case 'error': return '#721c24';
      case 'warning': return '#856404';
      default: return '#383d41';
    }
  }};
  border: 1px solid ${props => {
    switch (props.type) {
      case 'success': return '#c3e6cb';
      case 'error': return '#f5c6cb';
      case 'warning': return '#ffeaa7';
      default: return '#d6d8db';
    }
  }};
`;

const Table = styled.table`
  width: 100%;
  border-collapse: collapse;
  margin: 10px 0;
`;

const TableHeader = styled.th`
  background: ${props => props.theme.colors.primary};
  color: white;
  padding: 10px;
  text-align: left;
  font-weight: 500;
`;

const TableCell = styled.td`
  padding: 10px;
  border-bottom: 1px solid ${props => props.theme.colors.border};
`;

const TableRow = styled.tr`
  &:hover {
    background: ${props => props.theme.colors.hoverBackground};
  }
`;

const LoadingSpinner = styled.div`
  display: inline-block;
  width: 20px;
  height: 20px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid ${props => props.theme.colors.primary};
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-right: 10px;
  
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
`;

interface BackupInfo {
  backup_name: string;
  backup_path: string;
  created_at: string;
  backup_size_bytes: number;
  backup_size_mb: number;
  include_data?: boolean;
}

interface ExportInfo {
  export_name: string;
  export_path: string;
  created_at: string;
  export_size_bytes: number;
  export_size_mb: number;
  record_counts?: {
    users: number;
    ships: number;
    planets: number;
    teams: number;
    communications: number;
  };
}

interface ValidationResult {
  validated_at: string;
  checks: Array<{
    check: string;
    status: string;
    message: string;
  }>;
  errors: Array<{
    check: string;
    message: string;
    details?: any[];
  }>;
  warnings: Array<{
    check: string;
    message: string;
    details?: any[];
  }>;
  summary: {
    total_checks: number;
    passed_checks: number;
    total_errors: number;
    total_warnings: number;
    overall_status: string;
  };
}

const DataPersistence: React.FC = () => {
  const [backups, setBackups] = useState<BackupInfo[]>([]);
  const [exports, setExports] = useState<ExportInfo[]>([]);
  const [validationResults, setValidationResults] = useState<ValidationResult | null>(null);
  const [loading, setLoading] = useState<{ [key: string]: boolean }>({});
  const [statusMessage, setStatusMessage] = useState<{ type: 'success' | 'error' | 'warning', message: string } | null>(null);

  const dispatch = useAppDispatch();
  const { token } = useAppSelector(state => state.auth);

  useEffect(() => {
    loadBackups();
    loadExports();
  }, []);

  const setLoadingState = (key: string, value: boolean) => {
    setLoading(prev => ({ ...prev, [key]: value }));
  };

  const showStatusMessage = (type: 'success' | 'error' | 'warning', message: string) => {
    setStatusMessage({ type, message });
    setTimeout(() => setStatusMessage(null), 5000);
  };

  const loadBackups = async () => {
    try {
      setLoadingState('backups', true);
      const response = await api.get('/admin/data/backups', {
        headers: { Authorization: `Bearer ${token}` }
      });
      setBackups(response.data.backups);
    } catch (error) {
      showStatusMessage('error', 'Failed to load backups');
    } finally {
      setLoadingState('backups', false);
    }
  };

  const loadExports = async () => {
    try {
      setLoadingState('exports', true);
      const response = await api.get('/admin/data/exports', {
        headers: { Authorization: `Bearer ${token}` }
      });
      setExports(response.data.exports);
    } catch (error) {
      showStatusMessage('error', 'Failed to load exports');
    } finally {
      setLoadingState('exports', false);
    }
  };

  const createBackup = async () => {
    const backupName = (document.getElementById('backupName') as HTMLInputElement)?.value;
    const includeData = (document.getElementById('includeData') as HTMLInputElement)?.checked ?? true;

    try {
      setLoadingState('createBackup', true);
      const response = await api.post('/admin/data/backup', {
        backup_name: backupName || undefined,
        include_data: includeData
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      showStatusMessage('success', response.data.message);
      loadBackups();
    } catch (error) {
      showStatusMessage('error', 'Failed to create backup');
    } finally {
      setLoadingState('createBackup', false);
    }
  };

  const restoreBackup = async (backupName: string) => {
    if (!confirm(`Are you sure you want to restore backup "${backupName}"? This will overwrite the current database.`)) {
      return;
    }

    try {
      setLoadingState('restoreBackup', true);
      const response = await api.post('/admin/data/restore', {
        backup_name: backupName,
        confirm: true
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      showStatusMessage('success', response.data.message);
    } catch (error) {
      showStatusMessage('error', 'Failed to restore backup');
    } finally {
      setLoadingState('restoreBackup', false);
    }
  };

  const exportGameState = async () => {
    const exportName = (document.getElementById('exportName') as HTMLInputElement)?.value;
    const includeUsers = (document.getElementById('includeUsers') as HTMLInputElement)?.checked ?? true;
    const includeShips = (document.getElementById('includeShips') as HTMLInputElement)?.checked ?? true;
    const includePlanets = (document.getElementById('includePlanets') as HTMLInputElement)?.checked ?? true;
    const includeTeams = (document.getElementById('includeTeams') as HTMLInputElement)?.checked ?? true;
    const includeCommunications = (document.getElementById('includeCommunications') as HTMLInputElement)?.checked ?? true;

    try {
      setLoadingState('exportGameState', true);
      const response = await api.post('/admin/data/export', {
        export_name: exportName || undefined,
        include_users: includeUsers,
        include_ships: includeShips,
        include_planets: includePlanets,
        include_teams: includeTeams,
        include_communications: includeCommunications
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      showStatusMessage('success', response.data.message);
      loadExports();
    } catch (error) {
      showStatusMessage('error', 'Failed to export game state');
    } finally {
      setLoadingState('exportGameState', false);
    }
  };

  const importGameState = async (exportName: string) => {
    if (!confirm(`Are you sure you want to import game state from "${exportName}"? This will add data to the current database.`)) {
      return;
    }

    try {
      setLoadingState('importGameState', true);
      const response = await api.post('/admin/data/import', {
        export_name: exportName,
        confirm: true
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      showStatusMessage('success', response.data.message);
    } catch (error) {
      showStatusMessage('error', 'Failed to import game state');
    } finally {
      setLoadingState('importGameState', false);
    }
  };

  const validateDataIntegrity = async () => {
    try {
      setLoadingState('validateData', true);
      const response = await api.get('/admin/data/validate', {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setValidationResults(response.data);
      
      if (response.data.summary.overall_status === 'healthy') {
        showStatusMessage('success', 'Data integrity validation passed');
      } else {
        showStatusMessage('warning', `Data integrity validation found ${response.data.summary.total_errors} errors`);
      }
    } catch (error) {
      showStatusMessage('error', 'Failed to validate data integrity');
    } finally {
      setLoadingState('validateData', false);
    }
  };

  const cleanupBackups = async () => {
    const daysToKeep = parseInt((document.getElementById('daysToKeep') as HTMLInputElement)?.value || '30');

    try {
      setLoadingState('cleanupBackups', true);
      const response = await api.post('/admin/data/cleanup', {
        days_to_keep: daysToKeep
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      showStatusMessage('success', response.data.message);
      loadBackups();
    } catch (error) {
      showStatusMessage('error', 'Failed to cleanup backups');
    } finally {
      setLoadingState('cleanupBackups', false);
    }
  };

  return (
    <DataPersistenceContainer>
      <h1>Data Persistence Management</h1>
      
      {statusMessage && (
        <StatusMessage type={statusMessage.type}>
          {statusMessage.message}
        </StatusMessage>
      )}

      {/* Database Backups */}
      <Section>
        <SectionTitle>Database Backups</SectionTitle>
        
        <div style={{ marginBottom: '15px' }}>
          <Input
            id="backupName"
            type="text"
            placeholder="Backup name (optional)"
          />
          <Label>
            <Checkbox
              id="includeData"
              type="checkbox"
              defaultChecked
            />
            Include data
          </Label>
          <Button
            onClick={createBackup}
            disabled={loading.createBackup}
          >
            {loading.createBackup && <LoadingSpinner />}
            Create Backup
          </Button>
          <Button
            onClick={loadBackups}
            disabled={loading.backups}
          >
            {loading.backups && <LoadingSpinner />}
            Refresh
          </Button>
        </div>

        <Table>
          <thead>
            <tr>
              <TableHeader>Name</TableHeader>
              <TableHeader>Created</TableHeader>
              <TableHeader>Size</TableHeader>
              <TableHeader>Actions</TableHeader>
            </tr>
          </thead>
          <tbody>
            {backups.map((backup) => (
              <TableRow key={backup.backup_name}>
                <TableCell>{backup.backup_name}</TableCell>
                <TableCell>{new Date(backup.created_at).toLocaleString()}</TableCell>
                <TableCell>{backup.backup_size_mb} MB</TableCell>
                <TableCell>
                  <Button
                    variant="danger"
                    onClick={() => restoreBackup(backup.backup_name)}
                    disabled={loading.restoreBackup}
                  >
                    Restore
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </tbody>
        </Table>
      </Section>

      {/* Game State Export/Import */}
      <Section>
        <SectionTitle>Game State Export/Import</SectionTitle>
        
        <div style={{ marginBottom: '15px' }}>
          <Input
            id="exportName"
            type="text"
            placeholder="Export name (optional)"
          />
          <div style={{ margin: '10px 0' }}>
            <Label>
              <Checkbox
                id="includeUsers"
                type="checkbox"
                defaultChecked
              />
              Include Users
            </Label>
            <Label>
              <Checkbox
                id="includeShips"
                type="checkbox"
                defaultChecked
              />
              Include Ships
            </Label>
            <Label>
              <Checkbox
                id="includePlanets"
                type="checkbox"
                defaultChecked
              />
              Include Planets
            </Label>
            <Label>
              <Checkbox
                id="includeTeams"
                type="checkbox"
                defaultChecked
              />
              Include Teams
            </Label>
            <Label>
              <Checkbox
                id="includeCommunications"
                type="checkbox"
                defaultChecked
              />
              Include Communications
            </Label>
          </div>
          <Button
            onClick={exportGameState}
            disabled={loading.exportGameState}
          >
            {loading.exportGameState && <LoadingSpinner />}
            Export Game State
          </Button>
          <Button
            onClick={loadExports}
            disabled={loading.exports}
          >
            {loading.exports && <LoadingSpinner />}
            Refresh
          </Button>
        </div>

        <Table>
          <thead>
            <tr>
              <TableHeader>Name</TableHeader>
              <TableHeader>Created</TableHeader>
              <TableHeader>Size</TableHeader>
              <TableHeader>Records</TableHeader>
              <TableHeader>Actions</TableHeader>
            </tr>
          </thead>
          <tbody>
            {exports.map((export_item) => (
              <TableRow key={export_item.export_name}>
                <TableCell>{export_item.export_name}</TableCell>
                <TableCell>{new Date(export_item.created_at).toLocaleString()}</TableCell>
                <TableCell>{export_item.export_size_mb} MB</TableCell>
                <TableCell>
                  {export_item.record_counts && (
                    <div>
                      Users: {export_item.record_counts.users}<br/>
                      Ships: {export_item.record_counts.ships}<br/>
                      Planets: {export_item.record_counts.planets}
                    </div>
                  )}
                </TableCell>
                <TableCell>
                  <Button
                    variant="secondary"
                    onClick={() => importGameState(export_item.export_name)}
                    disabled={loading.importGameState}
                  >
                    Import
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </tbody>
        </Table>
      </Section>

      {/* Data Validation */}
      <Section>
        <SectionTitle>Data Integrity Validation</SectionTitle>
        
        <Button
          onClick={validateDataIntegrity}
          disabled={loading.validateData}
        >
          {loading.validateData && <LoadingSpinner />}
          Validate Data Integrity
        </Button>

        {validationResults && (
          <div style={{ marginTop: '20px' }}>
            <h3>Validation Results</h3>
            <p><strong>Overall Status:</strong> {validationResults.summary.overall_status}</p>
            <p><strong>Checks:</strong> {validationResults.summary.passed_checks}/{validationResults.summary.total_checks} passed</p>
            <p><strong>Errors:</strong> {validationResults.summary.total_errors}</p>
            <p><strong>Warnings:</strong> {validationResults.summary.total_warnings}</p>

            {validationResults.errors.length > 0 && (
              <div>
                <h4>Errors:</h4>
                {validationResults.errors.map((error, index) => (
                  <div key={index} style={{ margin: '10px 0', padding: '10px', background: '#f8d7da', borderRadius: '4px' }}>
                    <strong>{error.check}:</strong> {error.message}
                  </div>
                ))}
              </div>
            )}

            {validationResults.warnings.length > 0 && (
              <div>
                <h4>Warnings:</h4>
                {validationResults.warnings.map((warning, index) => (
                  <div key={index} style={{ margin: '10px 0', padding: '10px', background: '#fff3cd', borderRadius: '4px' }}>
                    <strong>{warning.check}:</strong> {warning.message}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </Section>

      {/* Backup Cleanup */}
      <Section>
        <SectionTitle>Backup Cleanup</SectionTitle>
        
        <div style={{ marginBottom: '15px' }}>
          <Label>
            Keep backups for:
            <Input
              id="daysToKeep"
              type="number"
              defaultValue="30"
              min="1"
              max="365"
              style={{ width: '80px', marginLeft: '10px' }}
            />
            days
          </Label>
          <Button
            onClick={cleanupBackups}
            disabled={loading.cleanupBackups}
          >
            {loading.cleanupBackups && <LoadingSpinner />}
            Cleanup Old Backups
          </Button>
        </div>
      </Section>
    </DataPersistenceContainer>
  );
};

export default DataPersistence;
