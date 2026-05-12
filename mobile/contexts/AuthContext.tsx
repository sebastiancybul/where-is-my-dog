import React, { createContext, useContext, useState, ReactNode, useEffect } from 'react';
import axios from 'axios';
import * as SecureStore from 'expo-secure-store';

interface User {
    id: number;
    username: string;
    email: string;
    phone: string | null;
    profile_photo: string | null;
    email_verified: boolean;
    is_moderator: boolean;
    is_banned: boolean;
    created_at: string;
}

interface LoginCredentials {
    email: string;
    password: string;
}

interface RegisterCredentials {
    username: string;
    email: string;
    password: string;
    password2: string;
    phone?: string;
}

interface AuthState {
    token: string | null;
    user: User | null;
    isLoading: boolean;
    isAuthenticated: boolean;
}

interface AuthContextType {
    authState: AuthState;
    onLogin: (credentials: LoginCredentials) => Promise<any>;
    onRegister: (credentials: RegisterCredentials) => Promise<any>;
    onLogout: () => Promise<void>;
    onUpdateUser: (data: Partial<User>) => void;
}

const API_URL = process.env.EXPO_PUBLIC_API_URL;

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
    const [authState, setAuthState] = useState<AuthState>({
        token: null,
        user: null,
        isLoading: true,
        isAuthenticated: false,
    });

    useEffect(() => {
        const loadToken = async () => {
            const access_token = await SecureStore.getItemAsync('access_token');
            
            if(access_token){

                axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;

                try {
                    const result = await axios.get(`${API_URL}/api/auth/me/`);
                    setAuthState({
                    token: access_token,
                    user: result.data,
                    isLoading: false,
                    isAuthenticated: true,
                    });
                } catch (e) {
                    await SecureStore.deleteItemAsync('access_token');
                    await SecureStore.deleteItemAsync('refresh_token');
                    delete axios.defaults.headers.common['Authorization'];
                    setAuthState({ token: null, user: null, isLoading: false, isAuthenticated: false });
                }
            } else {
                setAuthState(prev => ({ ...prev, isLoading: false }));
            }
        }
        loadToken();
    }, [])

    const register = async (credentials: RegisterCredentials) => {
        try {
            return await axios.post(`${API_URL}/api/auth/register/`, credentials)
        } catch (e) {
            const data = (e as any).response?.data;
            if(data){
                const firstKey = Object.keys(data)[0];
                const msg = `${data[firstKey][0]}`;
                return { error: true, msg };
            }
            return { error: true, msg: 'Something went wrong' };
        }
    };

    const login = async (credentials: LoginCredentials) => {
        try {
            const result =  await axios.post(`${API_URL}/api/auth/login/`, credentials)

            setAuthState({
                token: result.data.tokens.access,
                user: result.data.user,
                isLoading: false,
                isAuthenticated: true
            });

            axios.defaults.headers.common['Authorization'] = `Bearer ${result.data.tokens.access}`;


            await SecureStore.setItemAsync('access_token', result.data.tokens.access);
            await SecureStore.setItemAsync('refresh_token', result.data.tokens.refresh);

            return result

        } catch (e) {
            console.log((e as any).response)
            return { error: true, msg: (e as any).response?.data?.error || 'Something went wrong' }
        }
    };

    const logout = async () => {
        await SecureStore.deleteItemAsync('access_token');
        await SecureStore.deleteItemAsync('refresh_token');

        delete axios.defaults.headers.common['Authorization'];

        setAuthState({
            token: null,
            user: null,
            isLoading: false,
            isAuthenticated: false
        });
    }

    const updateUser = (data: Partial<User>) => {
        setAuthState(prev => ({ ...prev, user: { ...prev.user!, ...data } }));
    };

    const value = {
        onRegister: register,
        onLogin: login,
        onLogout: logout,
        onUpdateUser: updateUser,
        authState
    };


    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within AuthProvider');
    }
    return context;
}