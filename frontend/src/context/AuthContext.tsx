import React, { createContext, useContext, useState, useEffect } from 'react';
import { User, AuthState, UserRole } from '../types';

interface AuthContextType extends AuthState {
  login: (token: string, role: UserRole, username: string) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('sismowatch_token'));
  const [user, setUser] = useState<User | null>(() => {
    const saved = localStorage.getItem('sismowatch_user');
    return saved ? JSON.parse(saved) : null;
  });

  const login = (newToken: string, role: UserRole, username: string) => {
    const userObj: User = {
      id: 0,
      username,
      role,
      is_active: true,
      created_at: new Date().toISOString()
    };
    localStorage.setItem('sismowatch_token', newToken);
    localStorage.setItem('sismowatch_user', JSON.stringify(userObj));
    setToken(newToken);
    setUser(userObj);
  };

  const logout = () => {
    localStorage.removeItem('sismowatch_token');
    localStorage.removeItem('sismowatch_user');
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        token,
        user,
        isAuthenticated: !!token && !!user,
        isAdmin: user?.role === 'admin',
        login,
        logout
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
