import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { toast } from 'react-hot-toast';
import { useAppDispatch, useAppSelector } from '../../hooks/redux';
import { login, clearError } from '../../store/slices/authSlice';
import { LoginForm } from '../../types';
import styled from 'styled-components';

const LoginContainer = styled.div`
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%);
  padding: 20px;
`;

const LoginCard = styled.div`
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 16px;
  padding: 40px;
  width: 100%;
  max-width: 400px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5);
`;

const Title = styled.h1`
  text-align: center;
  font-size: 28px;
  font-weight: 700;
  margin-bottom: 8px;
  background: linear-gradient(135deg, #4ade80 0%, #22c55e 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
`;

const Subtitle = styled.p`
  text-align: center;
  color: #888;
  margin-bottom: 32px;
  font-size: 14px;
`;

const Form = styled.form`
  display: flex;
  flex-direction: column;
  gap: 20px;
`;

const FormGroup = styled.div`
  display: flex;
  flex-direction: column;
  gap: 8px;
`;

const Label = styled.label`
  font-size: 14px;
  font-weight: 500;
  color: #ccc;
`;

const Input = styled.input`
  padding: 12px 16px;
  background: #0a0a0a;
  border: 1px solid #333;
  border-radius: 8px;
  color: #fff;
  font-size: 14px;
  transition: border-color 0.2s ease;

  &:focus {
    outline: none;
    border-color: #4ade80;
    box-shadow: 0 0 0 3px rgba(74, 222, 128, 0.1);
  }

  &::placeholder {
    color: #666;
  }
`;

const ErrorMessage = styled.span`
  color: #f87171;
  font-size: 12px;
  margin-top: 4px;
`;

const Button = styled.button`
  padding: 14px;
  background: linear-gradient(135deg, #4ade80 0%, #22c55e 100%);
  border: none;
  border-radius: 8px;
  color: #000;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  margin-top: 8px;

  &:hover:not(:disabled) {
    background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
    transform: translateY(-1px);
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    transform: none;
  }
`;

const LinkText = styled.p`
  text-align: center;
  margin-top: 24px;
  color: #888;
  font-size: 14px;
`;

const StyledLink = styled(Link)`
  color: #4ade80;
  text-decoration: none;
  font-weight: 500;

  &:hover {
    text-decoration: underline;
  }
`;

const LoginPage: React.FC = () => {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { isLoading, error } = useAppSelector((state) => state.auth);
  
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginForm>();

  const onSubmit = async (data: LoginForm) => {
    try {
      await dispatch(login(data)).unwrap();
      toast.success('Login successful!');
      navigate('/dashboard');
    } catch (error) {
      toast.error(error as string);
    }
  };

  React.useEffect(() => {
    if (error) {
      toast.error(error);
      dispatch(clearError());
    }
  }, [error, dispatch]);

  return (
    <LoginContainer>
      <LoginCard>
        <Title>Galactic Empire</Title>
        <Subtitle>Welcome back, Commander</Subtitle>
        
        <Form onSubmit={handleSubmit(onSubmit)}>
          <FormGroup>
            <Label htmlFor="username">Username</Label>
            <Input
              id="username"
              type="text"
              placeholder="Enter your username"
              {...register('username', { required: 'Username is required' })}
            />
            {errors.username && (
              <ErrorMessage>{errors.username.message}</ErrorMessage>
            )}
          </FormGroup>

          <FormGroup>
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              placeholder="Enter your password"
              {...register('password', { required: 'Password is required' })}
            />
            {errors.password && (
              <ErrorMessage>{errors.password.message}</ErrorMessage>
            )}
          </FormGroup>

          <Button type="submit" disabled={isLoading}>
            {isLoading ? 'Signing In...' : 'Sign In'}
          </Button>
        </Form>

        <LinkText>
          Don't have an account?{' '}
          <StyledLink to="/register">Create one here</StyledLink>
        </LinkText>
      </LoginCard>
    </LoginContainer>
  );
};

export default LoginPage;
