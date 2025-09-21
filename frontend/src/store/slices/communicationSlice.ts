import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';

interface Message {
  id: number;
  sender_id: number;
  sender_name: string;
  recipient_id?: number;
  recipient_name?: string;
  subject: string;
  content: string;
  message_type: 'mail' | 'beacon' | 'team_chat' | 'distress';
  is_read: boolean;
  created_at: string;
}

interface CommunicationState {
  messages: Message[];
  unreadCount: number;
  isLoading: boolean;
  error: string | null;
  activeChannel: string;
}

const initialState: CommunicationState = {
  messages: [],
  unreadCount: 0,
  isLoading: false,
  error: null,
  activeChannel: 'mail',
};

// Async thunks
export const fetchMessages = createAsyncThunk(
  'communication/fetchMessages',
  async (channel: string, { rejectWithValue }) => {
    try {
      // This would be replaced with actual API calls
      return [];
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to fetch messages');
    }
  }
);

export const sendMessage = createAsyncThunk(
  'communication/sendMessage',
  async (messageData: Partial<Message>, { rejectWithValue }) => {
    try {
      // This would be replaced with actual API calls
      return messageData;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to send message');
    }
  }
);

export const markMessageAsRead = createAsyncThunk(
  'communication/markMessageAsRead',
  async (messageId: number, { rejectWithValue }) => {
    try {
      // This would be replaced with actual API calls
      return messageId;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to mark message as read');
    }
  }
);

const communicationSlice = createSlice({
  name: 'communication',
  initialState,
  reducers: {
    resetCommunicationState: (state) => {
      return initialState;
    },
    setActiveChannel: (state, action: PayloadAction<string>) => {
      state.activeChannel = action.payload;
    },
    addMessage: (state, action: PayloadAction<Message>) => {
      state.messages.unshift(action.payload);
      if (!action.payload.is_read) {
        state.unreadCount += 1;
      }
    },
    updateMessage: (state, action: PayloadAction<Message>) => {
      const index = state.messages.findIndex(msg => msg.id === action.payload.id);
      if (index !== -1) {
        const wasUnread = !state.messages[index].is_read;
        const isNowRead = action.payload.is_read;
        
        state.messages[index] = action.payload;
        
        if (wasUnread && isNowRead) {
          state.unreadCount = Math.max(0, state.unreadCount - 1);
        } else if (!wasUnread && !isNowRead) {
          state.unreadCount += 1;
        }
      }
    },
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch messages
      .addCase(fetchMessages.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchMessages.fulfilled, (state, action) => {
        state.isLoading = false;
        state.messages = action.payload;
        state.unreadCount = action.payload.filter(msg => !msg.is_read).length;
      })
      .addCase(fetchMessages.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })
      // Send message
      .addCase(sendMessage.fulfilled, (state, action) => {
        if (action.payload) {
          state.messages.unshift(action.payload as Message);
        }
      })
      // Mark message as read
      .addCase(markMessageAsRead.fulfilled, (state, action) => {
        const message = state.messages.find(msg => msg.id === action.payload);
        if (message && !message.is_read) {
          message.is_read = true;
          state.unreadCount = Math.max(0, state.unreadCount - 1);
        }
      });
  },
});

export const {
  resetCommunicationState,
  setActiveChannel,
  addMessage,
  updateMessage,
  clearError,
} = communicationSlice.actions;

export default communicationSlice.reducer;
